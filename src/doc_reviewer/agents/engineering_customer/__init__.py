"""Engineering customer agent package.

Re-exports public symbols so imports such as
``from doc_reviewer.agents.engineering_customer import ENGINEERING_INSTRUCTIONS``
keep working.
"""

from doc_reviewer.agents.engineering_customer.definition import (
    DESCRIPTION,
    FOUNDRY_AGENT_NAME,
    build_prompt_agent_definition,
)
from doc_reviewer.agents.engineering_customer.factory import AGENT_NAME, create_agent
from doc_reviewer.agents.engineering_customer.instructions import (
    ENGINEERING_INSTRUCTIONS,
)

__all__ = [
    "ENGINEERING_INSTRUCTIONS",
    "create_agent",
    "AGENT_NAME",
    "build_prompt_agent_definition",
    "FOUNDRY_AGENT_NAME",
    "DESCRIPTION",
]
