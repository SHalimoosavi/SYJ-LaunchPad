#!/usr/bin/env bash
# Runs Slither against contracts/src, or skips cleanly if there's nothing
# to analyze yet. See docs/CONTRACTS_TOOLCHAIN.md for why this check
# exists: Slither's Foundry integration errors out (not "0 findings", an
# actual failure) against an empty src/, and we don't fabricate a
# placeholder contract just to give it something to chew on.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d src ]; then
  # A missing src/ directory is a repository anomaly, not the normal
  # "no contracts yet" state — fail loudly rather than silently treating
  # it the same as an empty (but present) directory.
  echo "ERROR: contracts/src/ does not exist. This is unexpected — refusing to silently skip." >&2
  exit 1
fi

if find src -name '*.sol' -type f | grep -q .; then
  slither src/
else
  echo "No contract source in src/ yet — Slither has nothing to analyze. Skipping (not a failure). See docs/CONTRACTS_TOOLCHAIN.md."
fi
