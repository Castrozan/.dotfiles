#!/usr/bin/env bash
# Run all tests
# Usage: ./tests/run-tests.sh [--ci] [--coverage]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CI_MODE=false
COVERAGE_MODE=false
RUNTIME_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --ci) CI_MODE=true; shift ;;
        --coverage) COVERAGE_MODE=true; shift ;;
        --runtime) RUNTIME_MODE=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "=== Running Tests ==="
echo ""

# Skill validation
echo "--- Skill Validation ---"
"$SCRIPT_DIR/validate-agents.sh" "$SCRIPT_DIR/../agents/skills"
echo ""

# Script tests (bats) - with or without coverage
if [[ "$COVERAGE_MODE" == "true" ]]; then
    if command -v kcov &> /dev/null && command -v bats &> /dev/null; then
        echo "--- Script Tests with Coverage ---"
        "$SCRIPT_DIR/coverage.sh"
    else
        echo "WARN: kcov or bats not installed, skipping coverage"
        echo "      Install with: nix shell nixpkgs#kcov nixpkgs#bats"
    fi
elif command -v bats &> /dev/null; then
    echo "--- Script Tests (bats) ---"
    bats "$SCRIPT_DIR/scripts/"
else
    if [[ "$CI_MODE" == "true" ]]; then
        echo "SKIP: bats not installed"
    else
        echo "WARN: bats not installed, skipping script tests"
        echo "      Install with: nix shell nixpkgs#bats"
    fi
fi

# OpenClaw nix evaluation tests
if command -v nix &> /dev/null && command -v bats &> /dev/null; then
    echo "--- OpenClaw Evaluation Tests (bats + nix eval) ---"
    bats "$SCRIPT_DIR/openclaw/eval.bats"
else
    if [[ "$CI_MODE" == "true" ]]; then
        echo "SKIP: nix or bats not installed for openclaw eval tests"
    else
        echo "WARN: nix or bats not installed, skipping openclaw eval tests"
    fi
fi
echo ""

# OpenClaw runtime integration tests (opt-in, requires running gateway)
if [[ "$RUNTIME_MODE" == "true" ]]; then
    if command -v bats &> /dev/null; then
        echo "--- OpenClaw Runtime Tests (bats) ---"
        bats "$SCRIPT_DIR/openclaw/runtime.bats"
    else
        echo "WARN: bats not installed, skipping runtime tests"
    fi
    echo ""
fi

echo "=== All Tests Complete ==="
