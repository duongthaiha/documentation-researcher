"""Shared scaffolding for deploying agents to Azure AI Foundry as prompt agents.

Deployment requires the optional ``deploy`` dependencies::

    pip install "doc-reviewer[deploy]"   # azure-ai-projects

All ``deploy.py`` modules in the per-agent packages delegate here so the publish
logic lives in one place. Deploys default to ``dry_run=True`` so nothing is
published unless explicitly requested.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from doc_reviewer.config import Settings

if TYPE_CHECKING:
    from azure.ai.projects.models import AgentDefinition


def deploy_prompt_agent(
    settings: Settings,
    agent_name: str,
    definition: "AgentDefinition",
    *,
    description: str | None = None,
    metadata: dict[str, str] | None = None,
    dry_run: bool = True,
) -> Any:
    """Create (or version) a prompt agent in the configured Foundry project.

    Args:
        settings: Loaded application settings (provides the project endpoint).
        agent_name: The stable agent name to create/version in Foundry.
        definition: A ``PromptAgentDefinition`` describing the agent.
        description: Optional human-readable description.
        metadata: Optional string metadata stored alongside the agent version.
        dry_run: When True (default) nothing is published; the intended action
            is printed instead.

    Returns:
        The created ``AgentVersionDetails`` when published, else ``None``.
    """
    if dry_run:
        print(
            f"[dry-run] Would create/version prompt agent '{agent_name}' "
            f"on {settings.project_endpoint} "
            f"(model={settings.model_deployment_name})."
        )
        return None

    # Imported lazily so the core runtime does not require azure-ai-projects.
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=settings.project_endpoint,
            credential=credential,
        ) as client,
    ):
        result = client.agents.create_version(
            agent_name,
            definition=definition,
            description=description,
            metadata=metadata or {},
        )
        version = getattr(result, "id", None) or getattr(result, "name", agent_name)
        print(f"✅ Deployed prompt agent '{agent_name}' (version ref: {version}).")
        return result


def run_deploy_cli(
    deploy_fn: Any,
    *,
    prog: str,
) -> None:
    """Tiny argparse wrapper shared by per-agent ``deploy.py`` ``main()`` funcs.

    ``deploy_fn`` must accept ``(settings, *, dry_run)``.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog=prog,
        description=f"Deploy the {prog} prompt agent to Azure AI Foundry.",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Actually publish (default is a dry run).",
    )
    args = parser.parse_args()

    try:
        settings = Settings.from_env()
    except ValueError as exc:
        print(f"❌ Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    deploy_fn(settings, dry_run=not args.publish)
