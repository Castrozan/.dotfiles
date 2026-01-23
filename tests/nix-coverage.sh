#!/usr/bin/env bash
# Check Nix module coverage - identifies unused .nix files
# Usage: ./tests/nix-coverage.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Nix Module Coverage ==="
echo ""
echo "Checking which .nix files are imported by the flake..."
echo ""

# Get all .nix files in the repo (excluding result symlinks)
ALL_NIX_FILES=$(find "$REPO_DIR" -name "*.nix" -not -path "*/result/*" -not -path "*/.git/*" | sort)
TOTAL_FILES=$(echo "$ALL_NIX_FILES" | wc -l)

# Get files that are actually evaluated by the flake
# This uses nix-store --query to find runtime dependencies
echo "Building dependency graph (this may take a moment)..."

IMPORTED_FILES=$(
    nix path-info --derivation "$REPO_DIR#homeConfigurations.lucas.zanoni@x86_64-linux.activationPackage" 2>/dev/null |
    xargs nix derivation show 2>/dev/null |
    grep -oP '"'"$REPO_DIR"'/[^"]+\.nix"' |
    tr -d '"' |
    sort -u
) || IMPORTED_FILES=""

# If that didn't work, use a simpler heuristic - check what's imported
if [[ -z "$IMPORTED_FILES" ]]; then
    echo "Using import analysis instead..."
    IMPORTED_FILES=$(
        # Find all files mentioned in imports
        grep -rh "import \./\|imports = \[" "$REPO_DIR" --include="*.nix" 2>/dev/null |
        grep -oP '\./[a-zA-Z0-9_/-]+\.nix|\./[a-zA-Z0-9_/-]+(?=/default\.nix)' |
        sort -u
    ) || true
fi

echo ""
echo "=== Files by Directory ==="

# Group files by directory and show counts
echo "$ALL_NIX_FILES" | while read -r file; do
    dir=$(dirname "$file" | sed "s|$REPO_DIR/||")
    echo "$dir"
done | sort | uniq -c | sort -rn | head -20

echo ""
echo "=== Summary ==="
echo "Total .nix files: $TOTAL_FILES"

# Check for obviously unused patterns
echo ""
echo "=== Potential Issues ==="

# Check for .nix files not in any imports list
ORPHANS=()
for file in $ALL_NIX_FILES; do
    basename=$(basename "$file")
    dirname=$(dirname "$file")

    # Skip flake.nix, default.nix at root
    [[ "$basename" == "flake.nix" ]] && continue
    [[ "$file" == "$REPO_DIR/default.nix" ]] && continue

    # Check if this file is imported somewhere
    # default.nix can be imported via directory path
    if [[ "$basename" == "default.nix" ]]; then
        parent_dir=$(basename "$dirname")
        if ! grep -rq "$parent_dir\|$parent_dir/" "$REPO_DIR" --include="*.nix" 2>/dev/null; then
            ORPHANS+=("$file")
        fi
    elif ! grep -rq "$basename" "$REPO_DIR" --include="*.nix" 2>/dev/null; then
        ORPHANS+=("$file")
    fi
done

if [[ ${#ORPHANS[@]} -gt 0 ]]; then
    echo "Potentially unused files (not found in imports):"
    for f in "${ORPHANS[@]}"; do
        echo "  - ${f#$REPO_DIR/}"
    done
else
    echo "All .nix files appear to be imported."
fi

echo ""
echo "Note: Nix is declarative - 'coverage' means module usage, not line execution."
echo "For function-level testing, consider nix-unit."
