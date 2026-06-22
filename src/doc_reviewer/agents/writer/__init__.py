"""Writer agent package.

Re-exports public symbols so imports such as
``from doc_reviewer.agents.writer import WRITER_INSTRUCTIONS`` keep working.
"""

from doc_reviewer.agents.writer.definition import (
    DESCRIPTION,
    FOUNDRY_AGENT_NAME,
    build_prompt_agent_definition,
)
from doc_reviewer.agents.writer.factory import AGENT_NAME, create_agent
from doc_reviewer.agents.writer.instructions import WRITER_INSTRUCTIONS

__all__ = [
    "WRITER_INSTRUCTIONS",
    "create_agent",
    "AGENT_NAME",
    "build_prompt_agent_definition",
    "FOUNDRY_AGENT_NAME",
    "DESCRIPTION",
]
