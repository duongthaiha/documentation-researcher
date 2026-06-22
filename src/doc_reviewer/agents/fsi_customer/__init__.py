"""FSI customer agent package.

Re-exports the public symbols so existing imports such as
``from doc_reviewer.agents.fsi_customer import FSI_INSTRUCTIONS`` keep working.
"""

from doc_reviewer.agents.fsi_customer.definition import (
    DESCRIPTION,
    FOUNDRY_AGENT_NAME,
    build_prompt_agent_definition,
)
from doc_reviewer.agents.fsi_customer.factory import AGENT_NAME, create_agent
from doc_reviewer.agents.fsi_customer.instructions import FSI_INSTRUCTIONS

__all__ = [
    "FSI_INSTRUCTIONS",
    "create_agent",
    "AGENT_NAME",
    "build_prompt_agent_definition",
    "FOUNDRY_AGENT_NAME",
    "DESCRIPTION",
]
