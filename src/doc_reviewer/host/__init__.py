"""Host the documentation-reviewer **orchestrator** as a Foundry Hosted Agent.

The sub-agents (customers, research, writer) are deployed separately as Foundry
*prompt agents*. This package wraps the orchestration loop
(:func:`doc_reviewer.orchestrator.run_review_hosted`) in a Foundry **Hosted Agent**
(Pro-code) using the *Responses* protocol, so the whole two-phase review can be
invoked as a single managed Azure endpoint.

See ``README.md`` in this package for the deploy runbook.
"""

from doc_reviewer.host.server import (
    ReviewRequest,
    create_app,
    parse_review_request,
    run,
)

__all__ = ["ReviewRequest", "create_app", "parse_review_request", "run"]
