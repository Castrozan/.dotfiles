#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPOSITORY_DIR="$(dirname "$SCRIPT_DIR")"
readonly COVERAGE_OUTPUT_DIR="$SCRIPT_DIR/coverage"

main() {
  local ciMode=false

  _parse_arguments "$@"
  _require_command kcov "nix shell nixpkgs#kcov"
  _require_command bats "nix shell nixpkgs#bats"
  _clean_previous_coverage
  _run_bats_through_kcov
  _print_coverage_summary
  _print_per_file_coverage
}

_parse_arguments() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --html) shift ;;
      --ci) ciMode=true; shift ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done
}

_require_command() {
  local commandName="$1"
  local installHint="$2"
  if ! command -v "$commandName" &>/dev/null; then
    echo "ERROR: $commandName not found" >&2
    echo "Install with: $installHint" >&2
    exit 1
  fi
}

_clean_previous_coverage() {
  rm -rf "$COVERAGE_OUTPUT_DIR"
  mkdir -p "$COVERAGE_OUTPUT_DIR"
}

_run_bats_through_kcov() {
  echo "=== Running tests with coverage ==="
  echo ""
  kcov \
    --bash-dont-parse-binary-dir \
    --include-pattern="$REPOSITORY_DIR/bin/" \
    "$COVERAGE_OUTPUT_DIR" \
    bats "$SCRIPT_DIR/bin-scripts/"
}

_print_coverage_summary() {
  local coberturaFile="$COVERAGE_OUTPUT_DIR/bats/cobertura.xml"

  echo ""
  echo "=== Coverage Summary ==="

  if [[ ! -f "$coberturaFile" ]]; then
    echo "No coverage data found" >&2
    exit 1
  fi

  local lineRate linesCovered linesValid coveragePercent
  lineRate=$(grep -oP 'line-rate="\K[^"]+' "$coberturaFile" | head -1)
  linesCovered=$(grep -oP 'lines-covered="\K[^"]+' "$coberturaFile" | head -1)
  linesValid=$(grep -oP 'lines-valid="\K[^"]+' "$coberturaFile" | head -1)
  coveragePercent=$(echo "$lineRate * 100" | bc -l | xargs printf "%.1f")

  echo "Line coverage: ${coveragePercent}% (${linesCovered}/${linesValid} lines)"
  echo ""
  echo "Coverage report: $COVERAGE_OUTPUT_DIR/bats/index.html"
  echo "Cobertura XML: $coberturaFile"

  if [[ "$ciMode" == "true" ]]; then
    echo ""
    echo "::notice::Coverage: ${coveragePercent}% (${linesCovered}/${linesValid} lines)"
  fi
}

_print_per_file_coverage() {
  local coberturaFile="$COVERAGE_OUTPUT_DIR/bats/cobertura.xml"

  echo ""
  echo "=== Per-file Coverage ==="
  grep -oP 'filename="\K[^"]+' "$coberturaFile" | while read -r coveredFile; do
    local fileLineRate filePercent
    fileLineRate=$(grep "filename=\"$coveredFile\"" "$coberturaFile" | grep -oP 'line-rate="\K[^"]+')
    filePercent=$(echo "$fileLineRate * 100" | bc -l | xargs printf "%.0f")
    printf "  %-30s %3s%%\n" "$(basename "$coveredFile")" "$filePercent"
  done
}

main "$@"
