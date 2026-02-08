"""
Regulatory Agent using LangGraph for orchestrated conversations.

This agent provides an intelligent interface for navigating Health Canada
medical device regulations, combining:
- Tool-based classification and pathway guidance
- RAG-based document retrieval
- Conversational memory
"""

import operator
from typing import Annotated, Any, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from configs.settings import settings
from src.agents.tools import get_agent_tools
from src.utils.logging import get_logger

logger = get_logger(__name__)


# System prompt for the regulatory agent
SYSTEM_PROMPT = """You are an expert Health Canada medical device regulatory affairs specialist.
Your role is to help medical device manufacturers understand and navigate Canadian regulatory requirements.

You have access to tools that can:
1. Classify medical devices according to Health Canada rules and IMDRF SaMD framework
2. Generate regulatory pathways with timelines and fees
3. Create comprehensive submission checklists
4. Search official Health Canada guidance documents
5. Provide fee information

When helping users:
- Always gather enough information about the device before classifying
- For software devices (SaMD), ask about healthcare situation and significance
- Explain classifications with clear rationale citing specific regulations
- Provide actionable next steps
- Cite official guidance documents when available
- Be precise about timelines and fees, noting they are estimates

Key regulatory concepts:
- MDEL (Medical Device Establishment Licence): Required for any company selling devices in Canada
- MDL (Medical Device Licence): Required for Class II, III, IV devices
- Device Classes: I (lowest risk) to IV (highest risk)
- SaMD: Software as Medical Device, classified using IMDRF framework
- IMDRF ToC: International Medical Device Regulators Forum Table of Contents format for submissions

Always be helpful, accurate, and cite your sources when discussing regulations."""


class AgentState(TypedDict):
    """State maintained throughout the agent conversation."""

    messages: Annotated[list[BaseMessage], operator.add]
    device_info: dict[str, Any] | None
    classification_result: dict[str, Any] | None
    pathway_result: dict[str, Any] | None
    checklist_result: dict[str, Any] | None


class RegulatoryAgent:
    """
    Conversational agent for Health Canada medical device regulatory guidance.

    Uses LangGraph for orchestration with tool-calling capabilities.
    """

    def __init__(
        self,
        model_name: str | None = None,
        temperature: float = 0.1,
    ):
        self.logger = get_logger(self.__class__.__name__)
        self.model_name = model_name or settings.default_llm_model
        self.temperature = temperature

        # Initialize LLM
        self.llm = self._create_llm()

        # Get tools
        self.tools = get_agent_tools()

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the graph
        self.graph = self._build_graph()

        # Conversation state
        self._state: AgentState = {
            "messages": [],
            "device_info": None,
            "classification_result": None,
            "pathway_result": None,
            "checklist_result": None,
        }

    def _create_llm(self) -> ChatAnthropic | ChatOpenAI:
        """Create the LLM instance based on configuration."""
        if "claude" in self.model_name.lower():
            return ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=settings.max_tokens,
                api_key=settings.anthropic_api_key,
            )
        else:
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=settings.max_tokens,
                api_key=settings.openai_api_key,
            )

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""

        # Define the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END,
            },
        )

        # Tools always return to agent
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    def _call_model(self, state: AgentState) -> dict[str, Any]:
        """Call the LLM with the current state."""
        messages = state["messages"]

        # Add system message if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response = self.llm_with_tools.invoke(messages)

        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> str:
        """Determine whether to continue with tools or end."""
        messages = state["messages"]
        last_message = messages[-1]

        # If there are tool calls, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"

        return "end"

    def chat(self, user_message: str) -> str:
        """
        Send a message and get a response.

        Args:
            user_message: User's message

        Returns:
            Agent's response
        """
        self.logger.info(f"User message: {user_message[:100]}...")

        # Add user message to state
        self._state["messages"].append(HumanMessage(content=user_message))

        # Run the graph
        result = self.graph.invoke(self._state)

        # Update state
        self._state = result

        # Get the last AI message
        for message in reversed(result["messages"]):
            if isinstance(message, AIMessage):
                response = str(message.content)
                self.logger.info(f"Agent response: {response[:100]}...")
                return response

        return "I apologize, but I couldn't generate a response. Please try again."

    def reset(self) -> None:
        """Reset the conversation state."""
        self._state = {
            "messages": [],
            "device_info": None,
            "classification_result": None,
            "pathway_result": None,
            "checklist_result": None,
        }
        self.logger.info("Conversation reset")

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get the conversation history."""
        history = []
        for message in self._state["messages"]:
            if isinstance(message, HumanMessage):
                history.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                history.append({"role": "assistant", "content": message.content})
        return history


# Simple non-LangGraph version for environments without LangGraph
class SimpleRegulatoryAgent:
    """
    Simplified agent without LangGraph dependency.

    Uses direct tool calling for basic functionality.
    """

    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.tools = get_agent_tools()
        self.conversation_history: list[dict[str, str]] = []

    def chat(self, user_message: str) -> str:
        """Process user message and generate response."""
        self.conversation_history.append({"role": "user", "content": user_message})

        # Simple keyword-based routing to tools
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

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            response = f"I encountered an error processing your request: {str(e)}"

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_classification_query(self, message: str) -> str:
        """Handle device classification queries."""
        return (
            "To classify your device, I need to know:\n\n"
            "1. **Device name** and description\n"
            "2. **Intended use** statement\n"
            "3. Is it **software-based** (SaMD)?\n"
            "4. Is it an **in-vitro diagnostic** (IVD)?\n"
            "5. Is it **implantable**?\n"
            "6. Is it **active** (powered)?\n\n"
            "For software devices, I'll also need:\n"
            "- Healthcare situation (critical/serious/non-serious)\n"
            "- Significance of information provided (treat/diagnose/drive/inform)\n\n"
            "Please provide these details and I'll classify your device."
        )

    def _handle_pathway_query(self, message: str) -> str:
        """Handle regulatory pathway queries."""
        # Try to extract device class from message
        for class_name in ["IV", "III", "II", "I"]:
            if (
                f"class {class_name.lower()}" in message.lower()
                or f"class{class_name.lower()}" in message.lower()
            ):
                from src.agents.tools import get_regulatory_pathway

                result = get_regulatory_pathway.invoke(
                    {
                        "device_class": class_name,
                        "is_software": "software" in message.lower(),
                        "has_mdel": False,
                        "has_qms_certificate": False,
                    }
                )
                return self._format_pathway_response(result)

        return (
            "To provide the regulatory pathway, please specify:\n\n"
            "1. **Device class** (I, II, III, or IV)\n"
            "2. Do you already have an **MDEL**?\n"
            "3. Do you have **ISO 13485** certification?\n"
            "4. Is this a **software device**?\n\n"
            "Or if you need help determining your device class, "
            "I can help you classify it first."
        )

    def _handle_checklist_query(self, message: str) -> str:
        """Handle checklist queries."""
        return (
            "I can generate a regulatory checklist for your device.\n\n"
            "Please provide:\n"
            "1. **Device class** (I, II, III, or IV)\n"
            "2. **Device name** and description\n"
            "3. Is it a **software device**?\n\n"
            "The checklist will include all required:\n"
            "- MDEL requirements\n"
            "- QMS documentation\n"
            "- MDL application items\n"
            "- Clinical evidence (for Class III/IV)\n"
            "- Cybersecurity documentation (for software)\n"
            "- Labeling requirements"
        )

    def _handle_fee_query(self, message: str) -> str:
        """Handle fee queries."""
        from src.agents.tools import get_fee_information

        # Try to extract device class
        for class_name in ["IV", "III", "II", "I"]:
            if f"class {class_name.lower()}" in message.lower():
                result = get_fee_information.invoke({"device_class": class_name})
                return self._format_fee_response(result)

        return (
            "Health Canada fees vary by device class. Please specify your device class:\n\n"
            "- **Class I**: No MDL required, MDEL fee only\n"
            "- **Class II**: Lowest MDL fee\n"
            "- **Class III**: Moderate MDL fee + annual fee\n"
            "- **Class IV**: Highest MDL fee + annual fee\n\n"
            "Which device class would you like fee information for?"
        )

    def _handle_general_query(self, message: str) -> str:
        """Handle general queries with document search."""
        return (
            "I'm your Health Canada Medical Device Regulatory Assistant. I can help with:\n\n"
            "1. **Device Classification** - Determine your device class (I-IV)\n"
            "2. **Regulatory Pathway** - Steps, timeline, and requirements\n"
            "3. **Documentation Checklist** - What you need for submission\n"
            "4. **Fee Information** - Current Health Canada fees\n"
            "5. **Regulation Search** - Find specific guidance\n\n"
            "What would you like help with?"
        )

    def _format_pathway_response(self, result: dict[str, Any]) -> str:
        """Format pathway result as readable text."""
        if "error" in result:
            return f"Error: {result['error']}"

        lines = [
            f"## {result['pathway_name']}",
            "",
            f"**Requires MDEL:** {'Yes' if result['requires_mdel'] else 'No (already have one)'}",
            f"**Requires MDL:** {'Yes' if result['requires_mdl'] else 'No'}",
            "",
            "### Steps:",
        ]

        for step in result["steps"]:
            lines.append(f"\n**{step['step_number']}. {step['name']}**")
            lines.append(f"   {step['description'][:200]}...")
            if step["duration_days"]:
                lines.append(f"   Duration: ~{step['duration_days']} days")
            if step["fees"]:
                lines.append(f"   Fee: ${step['fees']:,.0f} CAD")

        lines.extend(
            [
                "",
                "### Timeline:",
                f"- Minimum: {result['timeline']['min_days']} days",
                f"- Maximum: {result['timeline']['max_days']} days",
                "",
                "### Total Fees:",
                f"- **${result['fees']['total']:,.0f} CAD**",
            ]
        )

        return "\n".join(lines)

    def _format_fee_response(self, result: dict[str, Any]) -> str:
        """Format fee result as readable text."""
        if "error" in result:
            return f"Error: {result['error']}"

        lines = [
            f"## Health Canada Fees - Class {result['device_class']}",
            "",
            "| Fee Type | Amount |",
            "|----------|--------|",
            f"| MDEL Application | ${result['mdel_application_fee']:,} CAD |",
            f"| MDL Application | ${result['mdl_application_fee']:,} CAD |",
            f"| Annual Right-to-Sell | ${result['annual_right_to_sell_fee']:,} CAD |",
            f"| MDL Amendment | ${result['mdl_amendment_fee']:,} CAD |",
            "",
            f"*Fee schedule as of {result['fee_schedule_date']}*",
            "",
            "**Notes:**",
        ]

        for note in result["notes"]:
            lines.append(f"- {note}")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset conversation history."""
        self.conversation_history = []
