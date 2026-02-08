"""Agent orchestration and LangGraph workflows.

Sprint 4C: Added get_regulatory_agent singleton, workflow definitions,
detect_workflow, detect_task_type utilities.
"""

from src.agents.regulatory_agent import (
    WORKFLOW_DEFINITIONS,
    AgentState,
    RegulatoryAgent,
    SimpleRegulatoryAgent,
    detect_task_type,
    detect_workflow,
    get_regulatory_agent,
)
from src.agents.regulatory_twin_tools import (
    REGULATORY_TWIN_TOOLS,
    get_regulatory_twin_tools,
)
from src.agents.tools import get_agent_tools

__all__ = [
    "AgentState",
    "RegulatoryAgent",
    "SimpleRegulatoryAgent",
    "REGULATORY_TWIN_TOOLS",
    "WORKFLOW_DEFINITIONS",
    "detect_task_type",
    "detect_workflow",
    "get_agent_tools",
    "get_regulatory_agent",
    "get_regulatory_twin_tools",
]
