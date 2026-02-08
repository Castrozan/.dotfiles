#!/usr/bin/env bash
# Validate skill YAML frontmatter structure
# Checks skills with YAML frontmatter for required fields (name, description)
# Skills without YAML frontmatter are valid (markdown-only format)

set -euo pipefail

SKILLS_DIR="${1:-agents/skills}"
ERRORS=0
CHECKED=0
SKIPPED=0

validate_skill() {
    local skillFile="$1"
    local skillName
    skillName=$(basename "$(dirname "$skillFile")")

    # Skip skills without YAML frontmatter (markdown-only is valid)
    if ! head -1 "$skillFile" | grep -q "^---$"; then
        echo "SKIP: $skillName (no YAML frontmatter)"
        SKIPPED=$((SKIPPED + 1))
        return
    fi

    CHECKED=$((CHECKED + 1))

    # Extract YAML (between first two ---)
    local yaml
    yaml=$(sed -n '2,/^---$/p' "$skillFile" | head -n -1)

    # Check required fields
    for field in name description; do
        if ! echo "$yaml" | grep -q "^$field:"; then
            echo "ERROR: $skillName missing required field: $field"
            ERRORS=$((ERRORS + 1))
        fi
    done

    if [[ $ERRORS -eq 0 ]] || ! echo "$yaml" | grep -q "^name:\|^description:"; then
        echo "OK: $skillName"
    fi
}

echo "Validating skills in $SKILLS_DIR..."
echo ""

for skillFile in "$SKILLS_DIR"/*/SKILL.md; do
    if [[ -f "$skillFile" ]]; then
        validate_skill "$skillFile"
    fi
done

echo ""
echo "Checked: $CHECKED, Skipped: $SKIPPED"
if [[ $ERRORS -gt 0 ]]; then
    echo "FAILED: $ERRORS errors found"
    exit 1
else
    echo "PASSED: All validated skills OK"
fi
