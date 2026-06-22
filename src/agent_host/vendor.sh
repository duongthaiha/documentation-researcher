#!/usr/bin/env bash
# Vendor the doc_reviewer package into this hosted-agent deploy directory so the
# `import doc_reviewer` resolves from the ZIP root that azd uploads. Run this
# before `azd deploy` whenever the package source changes.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"

rm -rf "$here/doc_reviewer"
cp -r "$repo/src/doc_reviewer" "$here/doc_reviewer"
find "$here" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

echo "Vendored doc_reviewer into $here/doc_reviewer"
echo "Next: azd deploy"
