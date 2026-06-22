"""Deploy the Research agent to Foundry as a prompt agent."""

from __future__ import annotations

from doc_reviewer.agents._deploy_common import deploy_prompt_agent, run_deploy_cli
from doc_reviewer.agents.research.definition import (
    DESCRIPTION,
    FOUNDRY_AGENT_NAME,
    build_prompt_agent_definition,
)
from doc_reviewer.config import Settings


def deploy(settings: Settings, *, dry_run: bool = True):
    """Create/version the Research prompt agent in Foundry."""
    return deploy_prompt_agent(
        settings,
        FOUNDRY_AGENT_NAME,
        build_prompt_agent_definition(settings),
        description=DESCRIPTION,
        metadata={"kind": "research"},
        dry_run=dry_run,
    )


def main() -> None:
    run_deploy_cli(deploy, prog=FOUNDRY_AGENT_NAME)


if __name__ == "__main__":
    main()
