"""Research agent package.

Re-exports public symbols so imports such as
``from doc_reviewer.agents.research import RESEARCH_INSTRUCTIONS`` keep working.
"""

from doc_reviewer.agents.research.definition import (
    DESCRIPTION,
    FOUNDRY_AGENT_NAME,
    build_mcp_tools,
    build_prompt_agent_definition,
)
from doc_reviewer.agents.research.factory import AGENT_NAME, create_agent
from doc_reviewer.agents.research.instructions import RESEARCH_INSTRUCTIONS

__all__ = [
    "RESEARCH_INSTRUCTIONS",
    "create_agent",
    "AGENT_NAME",
    "build_prompt_agent_definition",
    "build_mcp_tools",
    "FOUNDRY_AGENT_NAME",
    "DESCRIPTION",
]
