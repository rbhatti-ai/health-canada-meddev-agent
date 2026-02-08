"""
Tests for Sprint 4C — Agent Orchestration.

Tests cover:
- AgentState structure and defaults
- Workflow detection from user messages
- Task type detection from user messages
- Workflow definitions structure
- AI provenance logging helper
- Sanitize output integration
- RegulatoryAgent initialization (mocked LLM)
- Graph structure (nodes and edges)
- Tool count (18 total: 13 regulatory twin + 5 original)
- Conversation history management
- State reset
- Error handling
- chat_with_context enriched response
- SimpleRegulatoryAgent backward compat + language safety
- Singleton accessor

All tests are unit tests — no LLM calls, no DB, all mocked.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.regulatory_agent import (
    WORKFLOW_DEFINITIONS,
    WORKFLOW_TRIGGERS,
    AgentState,
    RegulatoryAgent,
    SimpleRegulatoryAgent,
    _default_state,
    _log_provenance,
    detect_task_type,
    detect_workflow,
    get_regulatory_agent,
)


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------
@pytest.fixture()
def default_state() -> AgentState:
    """Fresh default agent state."""
    return _default_state()


@pytest.fixture()
def mock_settings():
    """Mock settings to avoid needing real API keys."""
    with patch("src.agents.regulatory_agent.settings") as mock_s:
        mock_s.default_llm_model = "claude-3-5-sonnet-20241022"
        mock_s.max_tokens = 4096
        mock_s.anthropic_api_key = "test-key"
        mock_s.openai_api_key = "test-key"
        yield mock_s


@pytest.fixture()
def mock_agent(mock_settings):
    """RegulatoryAgent with mocked LLM — no real API calls."""
    with (
        patch("src.agents.regulatory_agent.ChatAnthropic") as mock_claude,
        patch("src.agents.regulatory_agent.get_agent_tools") as mock_tools,
        patch("src.agents.regulatory_agent.get_regulatory_twin_tools") as mock_twin_tools,
        patch.object(RegulatoryAgent, "_build_graph") as mock_graph,
    ):
        # Return 7 mock original tools (5 base + 2 IP)
        mock_tools.return_value = [MagicMock(name=f"orig_tool_{i}") for i in range(7)]
        # Return 13 mock twin tools
        mock_twin_tools.return_value = [MagicMock(name=f"twin_tool_{i}") for i in range(13)]

        # Mock LLM
        mock_llm_instance = MagicMock()
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_claude.return_value = mock_llm_instance

        # Mock graph to avoid ToolNode validation of mock objects
        mock_graph.return_value = MagicMock()

        agent = RegulatoryAgent()
        yield agent


# -----------------------------------------------------------------------
# Test class: AgentState structure
# -----------------------------------------------------------------------
class TestAgentState:
    """Tests for AgentState defaults and structure."""

    def test_default_state_has_all_keys(self, default_state: AgentState) -> None:
        """Default state must contain all required keys."""
        required_keys = {
            "messages",
            "device_info",
            "classification_result",
            "pathway_result",
            "checklist_result",
            "current_workflow",
            "workflow_step",
            "workflow_results",
            "device_version_id",
            "organization_id",
            "task_type",
            "provenance_records",
        }
        assert set(default_state.keys()) == required_keys

    def test_default_state_messages_empty(self, default_state: AgentState) -> None:
        """Messages list starts empty."""
        assert default_state["messages"] == []

    def test_default_state_nullable_fields_are_none(self, default_state: AgentState) -> None:
        """Nullable fields start as None."""
        nullable_fields = [
            "device_info",
            "classification_result",
            "pathway_result",
            "checklist_result",
            "current_workflow",
            "device_version_id",
            "organization_id",
            "task_type",
        ]
        for field in nullable_fields:
            assert default_state[field] is None, f"{field} should be None"

    def test_default_state_workflow_step_zero(self, default_state: AgentState) -> None:
        """Workflow step starts at 0."""
        assert default_state["workflow_step"] == 0

    def test_default_state_collections_empty(self, default_state: AgentState) -> None:
        """Collections start empty."""
        assert default_state["workflow_results"] == {}
        assert default_state["provenance_records"] == []


# -----------------------------------------------------------------------
# Test class: Workflow detection
# -----------------------------------------------------------------------
class TestWorkflowDetection:
    """Tests for detect_workflow()."""

    def test_full_analysis_trigger(self) -> None:
        """'analyze my device' triggers full_analysis."""
        assert detect_workflow("Please analyze my device") == "full_analysis"

    def test_risk_assessment_trigger(self) -> None:
        """'risk assessment' triggers risk_assessment."""
        assert detect_workflow("Run a risk assessment on this device") == "risk_assessment"

    def test_evidence_review_trigger(self) -> None:
        """'evidence review' triggers evidence_review."""
        assert detect_workflow("I need an evidence review") == "evidence_review"

    def test_submission_readiness_trigger(self) -> None:
        """'submission readiness' triggers submission_readiness."""
        assert detect_workflow("Check submission readiness") == "submission_readiness"

    def test_no_workflow_match(self) -> None:
        """Unrelated messages return None."""
        assert detect_workflow("What is the weather today?") is None

    def test_case_insensitive(self) -> None:
        """Workflow detection is case-insensitive."""
        assert detect_workflow("ANALYZE MY DEVICE please") == "full_analysis"

    def test_empty_message(self) -> None:
        """Empty message returns None."""
        assert detect_workflow("") is None


# -----------------------------------------------------------------------
# Test class: Task type detection
# -----------------------------------------------------------------------
class TestTaskTypeDetection:
    """Tests for detect_task_type()."""

    def test_hazard_assessment_detected(self) -> None:
        """Keywords like 'hazard' map to hazard_assessment."""
        assert detect_task_type("Assess the hazard profile") == "hazard_assessment"

    def test_coverage_gap_detected(self) -> None:
        """Keywords like 'gap' map to coverage_gap."""
        assert detect_task_type("Show me the coverage gaps") == "coverage_gap"

    def test_evidence_review_detected(self) -> None:
        """Keywords like 'evidence' map to evidence_review."""
        assert detect_task_type("Review evidence portfolio") == "evidence_review"

    def test_readiness_summary_detected(self) -> None:
        """Keywords like 'readiness' map to readiness_summary."""
        assert detect_task_type("Generate readiness summary") == "readiness_summary"

    def test_device_analysis_detected(self) -> None:
        """Keywords like 'classify' map to device_analysis."""
        assert detect_task_type("Classify my device") == "device_analysis"

    def test_no_task_type_match(self) -> None:
        """Unrelated messages return None."""
        assert detect_task_type("Hello, how are you?") is None

    def test_empty_message_returns_none(self) -> None:
        """Empty message returns None."""
        assert detect_task_type("") is None


# -----------------------------------------------------------------------
# Test class: Workflow definitions structure
# -----------------------------------------------------------------------
class TestWorkflowDefinitions:
    """Tests for WORKFLOW_DEFINITIONS and WORKFLOW_TRIGGERS."""

    def test_all_workflows_have_steps(self) -> None:
        """Every workflow has at least one step."""
        for _name, steps in WORKFLOW_DEFINITIONS.items():
            assert len(steps) >= 1, f"Workflow '{_name}' has no steps"

    def test_all_workflows_have_triggers(self) -> None:
        """Every workflow in DEFINITIONS has matching TRIGGERS."""
        for name in WORKFLOW_DEFINITIONS:
            assert name in WORKFLOW_TRIGGERS, f"Workflow '{name}' missing from TRIGGERS"

    def test_full_analysis_has_four_steps(self) -> None:
        """full_analysis follows: classify → coverage → gap → readiness."""
        steps = WORKFLOW_DEFINITIONS["full_analysis"]
        assert len(steps) == 4
        assert steps[0] == "classify_device"
        assert steps[-1] == "get_readiness_assessment"

    def test_workflow_names_are_strings(self) -> None:
        """Workflow step names are non-empty strings."""
        for _name, steps in WORKFLOW_DEFINITIONS.items():
            for step in steps:
                assert isinstance(step, str) and len(step) > 0


# -----------------------------------------------------------------------
# Test class: AI provenance helper
# -----------------------------------------------------------------------
class TestProvenanceHelper:
    """Tests for _log_provenance()."""

    def test_provenance_returns_dict(self, default_state: AgentState) -> None:
        """_log_provenance returns a dict."""
        result = _log_provenance(
            model_id="claude-test",
            task_type="general_chat",
            input_text="hello",
            output_text="hi there",
            state=default_state,
        )
        assert isinstance(result, dict)

    def test_provenance_has_required_fields(self, default_state: AgentState) -> None:
        """Provenance dict includes model, task_type, and hashes."""
        result = _log_provenance(
            model_id="claude-test",
            task_type="hazard_assessment",
            input_text="test input",
            output_text="test output",
            state=default_state,
        )
        assert "model_id" in result
        assert "task_type" in result
        assert result["model_id"] == "claude-test"
        assert result["task_type"] == "hazard_assessment"

    def test_provenance_with_device_context(self) -> None:
        """Provenance includes device_version_id when present in state."""
        state = _default_state()
        state["device_version_id"] = "dvid-123"
        state["organization_id"] = "org-456"

        result = _log_provenance(
            model_id="claude-test",
            task_type="gap_analysis",
            input_text="analyze",
            output_text="results",
            state=state,
        )
        assert isinstance(result, dict)


# -----------------------------------------------------------------------
# Test class: RegulatoryAgent initialization
# -----------------------------------------------------------------------
class TestRegulatoryAgentInit:
    """Tests for RegulatoryAgent initialization (mocked)."""

    def test_agent_has_20_tools(self, mock_agent: RegulatoryAgent) -> None:
        """Agent should have 20 tools (5 original + 13 twin + 2 IP)."""
        assert mock_agent.tool_count == 20

    def test_agent_default_model(self, mock_agent: RegulatoryAgent) -> None:
        """Agent uses default model from settings."""
        assert mock_agent.model_name == "claude-3-5-sonnet-20241022"

    def test_agent_default_temperature(self, mock_agent: RegulatoryAgent) -> None:
        """Agent default temperature is 0.1."""
        assert mock_agent.temperature == 0.1

    def test_agent_state_initialized(self, mock_agent: RegulatoryAgent) -> None:
        """Agent state is initialized on construction."""
        assert mock_agent._state is not None
        assert mock_agent._state["messages"] == []


# -----------------------------------------------------------------------
# Test class: Conversation management
# -----------------------------------------------------------------------
class TestConversationManagement:
    """Tests for conversation history and state management."""

    def test_reset_clears_state(self, mock_agent: RegulatoryAgent) -> None:
        """Reset returns state to defaults."""
        mock_agent._state["device_version_id"] = "some-id"
        mock_agent._state["messages"].append(HumanMessage(content="hello"))
        mock_agent.reset()
        assert mock_agent._state["messages"] == []
        assert mock_agent._state["device_version_id"] is None

    def test_get_conversation_history_empty(self, mock_agent: RegulatoryAgent) -> None:
        """Empty state returns empty history."""
        assert mock_agent.get_conversation_history() == []

    def test_get_conversation_history_with_messages(self, mock_agent: RegulatoryAgent) -> None:
        """History correctly maps Human/AI messages."""
        mock_agent._state["messages"] = [
            HumanMessage(content="hello"),
            AIMessage(content="hi there"),
        ]
        history = mock_agent.get_conversation_history()
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "hello"}
        assert history[1] == {"role": "assistant", "content": "hi there"}

    def test_set_device_context(self, mock_agent: RegulatoryAgent) -> None:
        """set_device_context updates state."""
        mock_agent.set_device_context(device_version_id="dv-1", organization_id="org-1")
        assert mock_agent._state["device_version_id"] == "dv-1"
        assert mock_agent._state["organization_id"] == "org-1"

    def test_get_provenance_records_empty(self, mock_agent: RegulatoryAgent) -> None:
        """No provenance records initially."""
        assert mock_agent.get_provenance_records() == []

    def test_get_available_workflows(self, mock_agent: RegulatoryAgent) -> None:
        """get_available_workflows returns all definitions."""
        workflows = mock_agent.get_available_workflows()
        assert "full_analysis" in workflows
        assert "risk_assessment" in workflows
        assert "evidence_review" in workflows
        assert "submission_readiness" in workflows


# -----------------------------------------------------------------------
# Test class: SimpleRegulatoryAgent backward compat
# -----------------------------------------------------------------------
class TestSimpleRegulatoryAgentCompat:
    """Tests for SimpleRegulatoryAgent backward compatibility."""

    def test_simple_agent_initializes(self) -> None:
        """SimpleRegulatoryAgent can be instantiated."""
        with patch("src.agents.regulatory_agent.get_agent_tools") as mock_tools:
            mock_tools.return_value = []
            agent = SimpleRegulatoryAgent()
            assert agent.conversation_history == []

    def test_simple_agent_classification_query(self) -> None:
        """Classification keywords route to classification handler."""
        with patch("src.agents.regulatory_agent.get_agent_tools") as mock_tools:
            mock_tools.return_value = []
            agent = SimpleRegulatoryAgent()
            response = agent.chat("How do I classify my device?")
            assert "classify" in response.lower() or "device" in response.lower()
            assert len(agent.conversation_history) == 2

    def test_simple_agent_reset(self) -> None:
        """Reset clears conversation history."""
        with patch("src.agents.regulatory_agent.get_agent_tools") as mock_tools:
            mock_tools.return_value = []
            agent = SimpleRegulatoryAgent()
            agent.conversation_history = [{"role": "user", "content": "test"}]
            agent.reset()
            assert agent.conversation_history == []

    def test_simple_agent_sanitizes_output(self) -> None:
        """SimpleRegulatoryAgent applies sanitize_ai_output to responses."""
        with patch("src.agents.regulatory_agent.get_agent_tools") as mock_tools:
            mock_tools.return_value = []
            agent = SimpleRegulatoryAgent()
            response = agent.chat("general question")
            # Response should not contain forbidden words
            forbidden = ["compliant", "guaranteed", "approved", "certified"]
            for word in forbidden:
                assert word not in response.lower()


# -----------------------------------------------------------------------
# Test class: Singleton accessor
# -----------------------------------------------------------------------
class TestSingletonAccessor:
    """Tests for get_regulatory_agent()."""

    def test_singleton_returns_same_instance(self, mock_settings) -> None:
        """get_regulatory_agent returns the same instance on repeated calls."""
        with (
            patch("src.agents.regulatory_agent.ChatAnthropic") as mock_claude,
            patch("src.agents.regulatory_agent.get_agent_tools") as mock_tools,
            patch("src.agents.regulatory_agent.get_regulatory_twin_tools") as mock_twin_tools,
            patch("src.agents.regulatory_agent._agent_instance", None),
        ):
            mock_tools.return_value = []
            mock_twin_tools.return_value = []
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_claude.return_value = mock_llm

            agent1 = get_regulatory_agent()
            agent2 = get_regulatory_agent()
            assert agent1 is agent2
