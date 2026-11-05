#!/usr/bin/env bash
# Single entry point for local and CI runs: install Zola, build the site,
# then run the Python test suite against the built output.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

bash scripts/install-zola.sh
.bin/zola build
python3 -m unittest discover -s tests -v
