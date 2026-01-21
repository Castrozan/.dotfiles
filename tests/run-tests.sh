#!/usr/bin/env bash
# Run all tests
# Usage: ./tests/run-tests.sh [--ci]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CI_MODE="${1:-}"

echo "=== Running Tests ==="
echo ""

# Agent validation
echo "--- Agent Validation ---"
"$SCRIPT_DIR/validate-agents.sh" "$SCRIPT_DIR/../agents/subagent"
echo ""

# Script tests (bats)
if command -v bats &> /dev/null; then
    echo "--- Script Tests (bats) ---"
    bats "$SCRIPT_DIR/scripts/"
else
    if [[ "$CI_MODE" == "--ci" ]]; then
        echo "SKIP: bats not installed (install with: nix shell nixpkgs#bats)"
    else
        echo "WARN: bats not installed, skipping script tests"
        echo "      Install with: nix shell nixpkgs#bats"
    fi
fi

echo ""
echo "=== All Tests Complete ==="
