"""Agent definitions for the documentation reviewer.

Each agent is a self-contained package (``fsi_customer/``, ``manufacturing_customer/``,
``engineering_customer/``, ``research/``, ``writer/``) structured so it can run
locally via the Microsoft Agent Framework or be deployed to Azure AI Foundry as
a prompt agent. :mod:`doc_reviewer.agents.base` exposes the backwards-compatible
``create_*`` factory API.
"""
