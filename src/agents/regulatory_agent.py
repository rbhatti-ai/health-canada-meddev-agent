"""
Regulatory Agent — LangGraph Orchestration for Health Canada MedDev Platform.

Sprint 4C: Agent Orchestration
- Multi-step workflows: analyze → classify → trace → gap → readiness
- LangGraph StateGraph with conditional routing
- All 18 tools (13 regulatory twin + 5 original)
- AI provenance logging for every AI output
- Regulatory-safe language enforcement on all outputs
- Conversation memory with full state management

NOTE: This replaces the original regulatory_agent.py from Sprint 0.
SimpleRegulatoryAgent is preserved for backward compatibility (deprecated).
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from configs.settings import settings
from src.agents.prompts import (
    REGULATORY_AGENT_SYSTEM_PROMPT,
    build_contextualized_prompt,
    create_ai_provenance,
    get_available_task_types,
    provenance_to_db_dict,
    sanitize_ai_output,
    validate_regulatory_language,
)
from src.agents.regulatory_twin_tools import get_regulatory_twin_tools
from src.agents.tools import get_agent_tools
from src.utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Workflow definitions — named multi-step sequences
# ---------------------------------------------------------------------------
WORKFLOW_DEFINITIONS: dict[str, list[str]] = {
    "full_analysis": [
        "classify_device",
        "get_coverage_report",
        "run_gap_analysis",
        "get_readiness_assessment",
    ],
    "risk_assessment": [
        "get_trace_chain",
        "get_coverage_report",
        "run_gap_analysis",
        "get_critical_gaps",
    ],
    "evidence_review": [
        "get_evidence_for_device",
        "find_unlinked_evidence",
        "run_gap_analysis",
    ],
    "submission_readiness": [
        "run_gap_analysis",
        "get_critical_gaps",
        "get_readiness_assessment",
    ],
}

# Keywords that trigger named workflows
WORKFLOW_TRIGGERS: dict[str, list[str]] = {
    "full_analysis": ["analyze my device", "full analysis", "complete analysis", "analyze device"],
    "risk_assessment": ["risk assessment", "risk analysis", "hazard assessment", "risk review"],
    "evidence_review": ["evidence review", "evidence assessment", "review evidence"],
    "submission_readiness": [
        "submission readiness",
        "readiness assessment",
        "submission check",
        "am i ready",
    ],
}


# ---------------------------------------------------------------------------
# Agent state — extended with regulatory twin context
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    """State maintained throughout the agent conversation."""

    messages: Annotated[list[BaseMessage], operator.add]
    device_info: dict[str, Any] | None
    classification_result: dict[str, Any] | None
    pathway_result: dict[str, Any] | None
    checklist_result: dict[str, Any] | None
    # Sprint 4C additions
    current_workflow: str | None
    workflow_step: int
    workflow_results: dict[str, Any]
    device_version_id: str | None
    organization_id: str | None
    task_type: str | None
    provenance_records: list[dict[str, Any]]


def _default_state() -> AgentState:
    """Return a fresh default state."""
    return AgentState(
        messages=[],
        device_info=None,
        classification_result=None,
        pathway_result=None,
        checklist_result=None,
        current_workflow=None,
        workflow_step=0,
        workflow_results={},
        device_version_id=None,
        organization_id=None,
        task_type=None,
        provenance_records=[],
    )


# ---------------------------------------------------------------------------
# Utility: detect workflow from user message
# ---------------------------------------------------------------------------
def detect_workflow(message: str) -> str | None:
    """Detect if the user message triggers a named workflow.

    Returns workflow name or None.
    """
    message_lower = message.lower().strip()
    for workflow_name, triggers in WORKFLOW_TRIGGERS.items():
        for trigger in triggers:
            if trigger in message_lower:
                return workflow_name
    return None


def detect_task_type(message: str) -> str | None:
    """Map user message to a task type for prompt routing.

    Returns a task_type string matching get_available_task_types() or None.
    """
    message_lower = message.lower().strip()
    task_map: dict[str, list[str]] = {
        "hazard_assessment": ["hazard", "risk", "harm", "safety"],
        "coverage_gap": ["gap", "coverage", "missing", "incomplete"],
        "evidence_review": ["evidence", "verification", "validation", "test"],
        "readiness_summary": ["readiness", "submission", "ready"],
        "device_analysis": ["analyze", "analysis", "classify", "classification"],
    }
    for task_type, keywords in task_map.items():
        if any(kw in message_lower for kw in keywords):
            return task_type
    return None


# ---------------------------------------------------------------------------
# AI provenance helper
# ---------------------------------------------------------------------------
def _log_provenance(
    model_id: str,
    task_type: str,
    input_text: str,
    output_text: str,
    state: AgentState,
) -> dict[str, Any]:
    """Create a provenance record and append to state.

    Returns the provenance dict for DB insertion.
    """
    provenance = create_ai_provenance(
        model_id=model_id,
        task_type=task_type,
        input_text=input_text,
        output_text=output_text,
        device_version_id=state.get("device_version_id"),
        organization_id=state.get("organization_id"),
    )
    return provenance_to_db_dict(provenance)


# ---------------------------------------------------------------------------
# Main agent class
# ---------------------------------------------------------------------------
class RegulatoryAgent:
    """
    Conversational agent for Health Canada medical device regulatory guidance.

    Uses LangGraph for orchestration with tool-calling capabilities.
    Integrates all 18 tools (13 regulatory twin + 5 original).
    Enforces regulatory-safe language on all AI outputs.
    Logs AI provenance for every output.
    """

    def __init__(
        self,
        model_name: str | None = None,
        temperature: float = 0.1,
    ) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.model_name = model_name or settings.default_llm_model
        self.temperature = temperature

        # Initialize LLM
        self.llm = self._create_llm()

        # Combine ALL tools: 5 original + 13 regulatory twin = 18 total
        original_tools = get_agent_tools()
        twin_tools = get_regulatory_twin_tools()
        self.tools = original_tools + twin_tools

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the graph
        self.graph = self._build_graph()

        # Conversation state
        self._state: AgentState = _default_state()

    def _create_llm(self) -> ChatAnthropic | ChatOpenAI:
        """Create the LLM instance based on configuration."""
        if "claude" in self.model_name.lower():
            return ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=settings.max_tokens,
                api_key=settings.anthropic_api_key,
            )
        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key,
        )

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with conditional routing."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("router", self._route_message)
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("sanitize", self._sanitize_output)

        # Entry point is the router
        workflow.set_entry_point("router")

        # Router decides: go to agent
        workflow.add_edge("router", "agent")

        # Agent either calls tools or goes to sanitize
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": "sanitize",
            },
        )

        # Tools always return to agent
        workflow.add_edge("tools", "agent")

        # Sanitize is the terminal node
        workflow.add_edge("sanitize", END)

        return workflow.compile()

    def _route_message(self, state: AgentState) -> dict[str, Any]:
        """Route the incoming message — detect workflows and task types.

        This node enriches the state with workflow/task metadata
        before the agent node runs.
        """
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return {}

        user_text = last_message.content if isinstance(last_message.content, str) else ""

        updates: dict[str, Any] = {}

        # Detect named workflow
        workflow = detect_workflow(user_text)
        if workflow:
            updates["current_workflow"] = workflow
            updates["workflow_step"] = 0
            self.logger.info(f"Detected workflow: {workflow}")

        # Detect task type for prompt routing
        task_type = detect_task_type(user_text)
        if task_type:
            updates["task_type"] = task_type
            self.logger.info(f"Detected task type: {task_type}")

        return updates

    def _call_model(self, state: AgentState) -> dict[str, Any]:
        """Call the LLM with the current state and appropriate prompt."""
        messages = list(state.get("messages", []))

        # Select system prompt based on task type
        task_type = state.get("task_type")
        device_context = None
        if state.get("device_version_id"):
            device_context = {"device_version_id": state["device_version_id"]}

        if task_type and task_type in get_available_task_types():
            system_prompt = build_contextualized_prompt(
                task_type=task_type,
                device_context=device_context,
            )
        else:
            system_prompt = REGULATORY_AGENT_SYSTEM_PROMPT

        # Ensure system message is first
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + messages
        else:
            # Replace existing system message with task-appropriate one
            messages[0] = SystemMessage(content=system_prompt)

        response = self.llm_with_tools.invoke(messages)

        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> str:
        """Determine whether to continue with tools or end."""
        messages = state.get("messages", [])
        if not messages:
            return "end"

        last_message = messages[-1]

        # If there are tool calls, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"

        return "end"

    def _sanitize_output(self, state: AgentState) -> dict[str, Any]:
        """Sanitize the final AI output for regulatory-safe language.

        Also creates AI provenance record.
        """
        messages = state.get("messages", [])
        if not messages:
            return {}

        # Find the last AI message
        last_ai_message = None

        for i in range(len(messages) - 1, -1, -1):
            if isinstance(messages[i], AIMessage):
                last_ai_message = messages[i]

                break

        if last_ai_message is None:
            return {}

        original_content = (
            last_ai_message.content
            if isinstance(last_ai_message.content, str)
            else str(last_ai_message.content)
        )

        # Sanitize for regulatory-safe language
        sanitized_content = sanitize_ai_output(original_content)

        # Validate — log warnings for any remaining issues
        validation = validate_regulatory_language(sanitized_content)
        if not validation.get("is_valid", True):
            self.logger.warning(
                f"Language validation issues after sanitization: {validation.get('violations', [])}"
            )

        # Create provenance record
        user_input = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                user_input = content  # last user message

        provenance_dict = _log_provenance(
            model_id=self.model_name,
            task_type=state.get("task_type") or "general_chat",
            input_text=user_input,
            output_text=sanitized_content,
            state=state,
        )

        # Build updated provenance list
        existing_provenance = list(state.get("provenance_records", []))
        existing_provenance.append(provenance_dict)

        # If content was sanitized, create a new AI message
        if sanitized_content != original_content:
            new_message = AIMessage(content=sanitized_content)
            # We return the sanitized message to replace via state
            # LangGraph's add reducer will append, so we track this
            return {
                "messages": [new_message],
                "provenance_records": existing_provenance,
            }

        return {"provenance_records": existing_provenance}

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def chat(self, user_message: str) -> str:
        """Send a message and get a response.

        Args:
            user_message: User's message

        Returns:
            Agent's response (regulatory-safe, provenance-logged)
        """
        self.logger.info(f"User message: {user_message[:100]}...")

        # Add user message to state
        self._state["messages"].append(HumanMessage(content=user_message))

        # Run the graph
        try:
            result = self.graph.invoke(self._state)
        except Exception as e:
            self.logger.error(f"Graph invocation error: {e}")
            error_response = (
                "An error occurred while processing your request. "
                "Please try again or rephrase your question."
            )
            self._state["messages"].append(AIMessage(content=error_response))
            return error_response

        # Update state
        self._state = result

        # Get the last AI message
        for message in reversed(result.get("messages", [])):
            if isinstance(message, AIMessage):
                response = (
                    message.content if isinstance(message.content, str) else str(message.content)
                )
                self.logger.info(f"Agent response: {response[:100]}...")
                return response

        fallback = (
            "Unable to generate a response at this time. " "Please try rephrasing your question."
        )
        return fallback

    def chat_with_context(
        self,
        user_message: str,
        device_version_id: str | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a message with device/org context and get enriched response.

        Returns dict with 'response', 'provenance', 'workflow', 'task_type'.
        """
        if device_version_id:
            self._state["device_version_id"] = device_version_id
        if organization_id:
            self._state["organization_id"] = organization_id

        response_text = self.chat(user_message)

        return {
            "response": response_text,
            "provenance": self._state.get("provenance_records", []),
            "workflow": self._state.get("current_workflow"),
            "task_type": self._state.get("task_type"),
        }

    def reset(self) -> None:
        """Reset the conversation state."""
        self._state = _default_state()
        self.logger.info("Conversation reset")

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get the conversation history."""
        history: list[dict[str, str]] = []
        for message in self._state.get("messages", []):
            if isinstance(message, HumanMessage):
                content = (
                    message.content if isinstance(message.content, str) else str(message.content)
                )
                history.append({"role": "user", "content": content})
            elif isinstance(message, AIMessage):
                content = (
                    message.content if isinstance(message.content, str) else str(message.content)
                )
                history.append({"role": "assistant", "content": content})
        return history

    def get_provenance_records(self) -> list[dict[str, Any]]:
        """Get all AI provenance records from this session."""
        return list(self._state.get("provenance_records", []))

    def get_current_workflow(self) -> str | None:
        """Get the currently active workflow name, if any."""
        return self._state.get("current_workflow")

    def get_available_workflows(self) -> dict[str, list[str]]:
        """Get all available named workflows and their steps."""
        return dict(WORKFLOW_DEFINITIONS)

    def set_device_context(
        self,
        device_version_id: str | None = None,
        organization_id: str | None = None,
    ) -> None:
        """Set device/org context for subsequent interactions."""
        if device_version_id is not None:
            self._state["device_version_id"] = device_version_id
        if organization_id is not None:
            self._state["organization_id"] = organization_id

    @property
    def tool_count(self) -> int:
        """Return the number of bound tools."""
        return len(self.tools)


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------
_agent_instance: RegulatoryAgent | None = None


def get_regulatory_agent(
    model_name: str | None = None,
    temperature: float = 0.1,
) -> RegulatoryAgent:
    """Get or create the singleton RegulatoryAgent instance."""
    global _agent_instance  # noqa: PLW0603
    if _agent_instance is None:
        _agent_instance = RegulatoryAgent(
            model_name=model_name,
            temperature=temperature,
        )
    return _agent_instance


# ---------------------------------------------------------------------------
# SimpleRegulatoryAgent — DEPRECATED, kept for backward compatibility
# ---------------------------------------------------------------------------
class SimpleRegulatoryAgent:
    """Simplified agent without LangGraph dependency.

    .. deprecated::
        Use RegulatoryAgent instead. This class is preserved for backward
        compatibility with existing CLI and Streamlit integrations.
    """

    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.tools = get_agent_tools()
        self.conversation_history: list[dict[str, str]] = []

    def chat(self, user_message: str) -> str:
        """Process user message and generate response."""
        self.conversation_history.append({"role": "user", "content": user_message})

        message_lower = user_message.lower()

        try:
            if any(word in message_lower for word in ["classify", "class", "classification"]):
                response = self._handle_classification_query(user_message)
            elif any(word in message_lower for word in ["pathway", "steps", "process", "timeline"]):
                response = self._handle_pathway_query(user_message)
            elif any(word in message_lower for word in ["checklist", "documents", "requirements"]):
                response = self._handle_checklist_query(user_message)
            elif any(word in message_lower for word in ["fee", "cost", "price"]):
                response = self._handle_fee_query(user_message)
            else:
                response = self._handle_general_query(user_message)

        except RuntimeError as e:
            self.logger.error(f"Error processing message: {e}")
            response = f"An error occurred processing your request: {e}"

        # Sanitize output for regulatory safety
        response = sanitize_ai_output(response)

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_classification_query(self, message: str) -> str:
        """Handle device classification queries."""
        return (
            "To classify your device, I need to know:\n\n"
            "1. Device name and description\n"
            "2. Intended use statement\n"
            "3. Is it software-based (SaMD)?\n"
            "4. Is it an in-vitro diagnostic (IVD)?\n"
            "5. Is it implantable?\n"
            "6. Is it active (powered)?\n\n"
            "For software devices, I'll also need:\n"
            "- Healthcare situation (critical/serious/non-serious)\n"
            "- Significance of information provided (treat/diagnose/drive/inform)\n\n"
            "Please provide these details and I'll classify your device."
        )

    def _handle_pathway_query(self, message: str) -> str:
        """Handle regulatory pathway queries."""
        return (
            "To determine the regulatory pathway, I need the device classification first. "
            "If you haven't classified your device yet, please provide the device details "
            "and I can help with that."
        )

    def _handle_checklist_query(self, message: str) -> str:
        """Handle checklist queries."""
        return (
            "I can generate a submission checklist once I know your device class "
            "and regulatory pathway. Would you like to start with device classification?"
        )

    def _handle_fee_query(self, message: str) -> str:
        """Handle fee queries."""
        return (
            "Health Canada fees vary by device class. "
            "Please provide your device classification (Class I-IV) "
            "and I can look up the current fee schedule."
        )

    def _handle_general_query(self, message: str) -> str:
        """Handle general regulatory queries."""
        return (
            "I can help with Health Canada medical device regulatory questions including:\n"
            "- Device classification\n"
            "- Regulatory pathways (MDEL, MDL)\n"
            "- Submission checklists\n"
            "- Fee information\n"
            "- Regulatory guidance search\n\n"
            "What would you like to know?"
        )

    def reset(self) -> None:
        """Reset conversation history."""
        self.conversation_history = []
