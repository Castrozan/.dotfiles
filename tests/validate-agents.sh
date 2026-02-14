#!/usr/bin/env bash

set -Eeuo pipefail

readonly SKILLS_DIR="${1:-agents/skills}"

main() {
  local errorCount=0
  local checkedCount=0
  local skippedCount=0

  echo "Validating skills in $SKILLS_DIR..."
  echo ""

  for skillFile in "$SKILLS_DIR"/*/SKILL.md; do
    [[ -f "$skillFile" ]] || continue
    _validate_skill "$skillFile"
  done

  echo ""
  echo "Checked: $checkedCount, Skipped: $skippedCount"

  if [[ $errorCount -gt 0 ]]; then
    echo "FAILED: $errorCount errors found"
    exit 1
  fi

  echo "PASSED: All validated skills OK"
}

_validate_skill() {
  local skillFile="$1"
  local skillName
  skillName=$(basename "$(dirname "$skillFile")")

  if ! head -1 "$skillFile" | grep -q "^---$"; then
    echo "SKIP: $skillName (no YAML frontmatter)"
    skippedCount=$((skippedCount + 1))
    return
  fi

  checkedCount=$((checkedCount + 1))

  local yaml
  yaml=$(sed -n '2,/^---$/p' "$skillFile" | head -n -1)

  local hasError=false
  for field in name description; do
    if ! echo "$yaml" | grep -q "^$field:"; then
      echo "ERROR: $skillName missing required field: $field"
      errorCount=$((errorCount + 1))
      hasError=true
    fi
  done

  [[ "$hasError" == "false" ]] && echo "OK: $skillName"
}

main "$@"
