#!/usr/bin/env bash
# Validate agent YAML frontmatter structure
# Checks: required fields, model=opus, single-line description

set -euo pipefail

AGENTS_DIR="${1:-agents/subagent}"
ERRORS=0

validate_agent() {
    local agent="$1"
    local name
    name=$(basename "$agent")

    # Check YAML frontmatter exists
    if ! head -1 "$agent" | grep -q "^---$"; then
        echo "ERROR: $name missing YAML frontmatter"
        ((ERRORS++))
        return
    fi

    # Extract YAML (between first two ---)
    local yaml
    yaml=$(sed -n '2,/^---$/p' "$agent" | head -n -1)

    # Check required fields
    for field in name description model color; do
        if ! echo "$yaml" | grep -q "^$field:"; then
            echo "ERROR: $name missing required field: $field"
            ((ERRORS++))
        fi
    done

    # Check model is opus
    if ! echo "$yaml" | grep -q "^model: opus"; then
        echo "ERROR: $name has non-opus model (should be 'model: opus')"
        ((ERRORS++))
    fi

    # Check description is single-line quoted (starts with " and ends with ")
    local desc_line
    desc_line=$(echo "$yaml" | grep "^description:")
    if ! echo "$desc_line" | grep -qE '^description: ".*"$'; then
        echo "WARN: $name description may not be single-line quoted (required for Claude Code)"
    fi

    echo "OK: $name"
}

echo "Validating agents in $AGENTS_DIR..."
echo ""

for agent in "$AGENTS_DIR"/*.md; do
    if [[ -f "$agent" ]]; then
        validate_agent "$agent"
    fi
done

echo ""
if [[ $ERRORS -gt 0 ]]; then
    echo "FAILED: $ERRORS errors found"
    exit 1
else
    echo "PASSED: All agents valid"
fi
