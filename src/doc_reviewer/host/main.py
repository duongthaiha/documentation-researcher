"""Foundry Hosted Agent entrypoint (azd ``--deploy-mode code`` expects ``main.py``).

The hosting library starts an HTTP server that serves the Responses protocol and
dispatches requests to the handler registered in
:func:`doc_reviewer.host.server.create_app`.
"""

from doc_reviewer.host.server import run

if __name__ == "__main__":
    run()
