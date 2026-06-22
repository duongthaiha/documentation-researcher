# Container image for the doc-reviewer Hosted Agent (Responses protocol).
#
# Build from the REPOSITORY ROOT so the whole project is in the build context:
#
#   docker build -f src/doc_reviewer/host/Dockerfile -t doc-reviewer-orchestrator .
#
# Hosted agents require Python 3.13+.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the host's preview hosting deps first (better layer caching).
COPY src/doc_reviewer/host/requirements.txt /app/host-requirements.txt
RUN pip install --no-cache-dir -r /app/host-requirements.txt

# Install the doc-reviewer project itself (orchestrator + sub-agent registry).
COPY . /app
RUN pip install --no-cache-dir ".[host]"

# Start the Responses HTTP server. The hosting library handles the port,
# health checks, and OpenTelemetry integration.
CMD ["python", "-m", "doc_reviewer.host.main"]
