"""Manufacturing customer agent package.

Re-exports public symbols so imports such as
``from doc_reviewer.agents.manufacturing_customer import MANUFACTURING_INSTRUCTIONS``
keep working.
"""

from doc_reviewer.agents.manufacturing_customer.definition import (
    DESCRIPTION,
    FOUNDRY_AGENT_NAME,
    build_prompt_agent_definition,
)
from doc_reviewer.agents.manufacturing_customer.factory import (
    AGENT_NAME,
    create_agent,
)
from doc_reviewer.agents.manufacturing_customer.instructions import (
    MANUFACTURING_INSTRUCTIONS,
)

__all__ = [
    "MANUFACTURING_INSTRUCTIONS",
    "create_agent",
    "AGENT_NAME",
    "build_prompt_agent_definition",
    "FOUNDRY_AGENT_NAME",
    "DESCRIPTION",
]
