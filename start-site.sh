#!/usr/bin/env bash
#
# Starts the local AI Bureau Hugo preview server.
#
# Input: none.
# Output: local preview at http://localhost:1313/.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUGO_BIN="${PROJECT_DIR}/.tools/hugo/hugo"

if [[ ! -x "${HUGO_BIN}" ]]; then
  echo "Local Hugo binary is missing: ${HUGO_BIN}" >&2
  exit 1
fi

exec "${HUGO_BIN}" server \
  --source "${PROJECT_DIR}" \
  --buildDrafts \
  --disableFastRender \
  --navigateToChanged
