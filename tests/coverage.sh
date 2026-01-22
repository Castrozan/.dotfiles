#!/usr/bin/env bash
# Generate test coverage for shell scripts using kcov
# Usage: ./tests/coverage.sh [--html] [--ci]
#
# Requires: kcov (nix shell nixpkgs#kcov)
# Output: tests/coverage/ directory with HTML reports and cobertura.xml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
COVERAGE_DIR="$SCRIPT_DIR/coverage"
HTML_MODE=false
CI_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --html) HTML_MODE=true; shift ;;
        --ci) CI_MODE=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Check for kcov
if ! command -v kcov &> /dev/null; then
    echo "ERROR: kcov not found"
    echo "Install with: nix shell nixpkgs#kcov"
    exit 1
fi

# Check for bats
if ! command -v bats &> /dev/null; then
    echo "ERROR: bats not found"
    echo "Install with: nix shell nixpkgs#bats"
    exit 1
fi

# Clean previous coverage
rm -rf "$COVERAGE_DIR"
mkdir -p "$COVERAGE_DIR"

echo "=== Running tests with coverage ==="
echo ""

# Run bats tests through kcov
kcov \
    --bash-dont-parse-binary-dir \
    --include-pattern="$REPO_DIR/bin/" \
    "$COVERAGE_DIR" \
    bats "$SCRIPT_DIR/scripts/"

echo ""
echo "=== Coverage Summary ==="

# Extract coverage from cobertura.xml
COBERTURA="$COVERAGE_DIR/bats/cobertura.xml"
if [[ -f "$COBERTURA" ]]; then
    LINE_RATE=$(grep -oP 'line-rate="\K[^"]+' "$COBERTURA" | head -1)
    LINES_COVERED=$(grep -oP 'lines-covered="\K[^"]+' "$COBERTURA" | head -1)
    LINES_VALID=$(grep -oP 'lines-valid="\K[^"]+' "$COBERTURA" | head -1)

    PERCENT=$(echo "$LINE_RATE * 100" | bc -l | xargs printf "%.1f")

    echo "Line coverage: ${PERCENT}% (${LINES_COVERED}/${LINES_VALID} lines)"
    echo ""
    echo "Coverage report: $COVERAGE_DIR/bats/index.html"
    echo "Cobertura XML: $COBERTURA"

    if [[ "$CI_MODE" == "true" ]]; then
        # Output for CI (GitHub Actions)
        echo ""
        echo "::notice::Coverage: ${PERCENT}% (${LINES_COVERED}/${LINES_VALID} lines)"
    fi
else
    echo "No coverage data found"
    exit 1
fi

# Per-file coverage
echo ""
echo "=== Per-file Coverage ==="
grep -oP 'filename="\K[^"]+' "$COBERTURA" | while read -r file; do
    rate=$(grep "filename=\"$file\"" "$COBERTURA" | grep -oP 'line-rate="\K[^"]+')
    pct=$(echo "$rate * 100" | bc -l | xargs printf "%.0f")
    basename=$(basename "$file")
    printf "  %-30s %3s%%\n" "$basename" "$pct"
done
