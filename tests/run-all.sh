#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

main() {
  local ciMode=false
  local coverageMode=false
  local runtimeMode=false

  _parse_arguments "$@"

  echo "=== Running Tests ==="
  echo ""

  _run_skill_frontmatter_validation
  _run_bin_script_tests
  _run_home_manager_module_tests
  _run_openclaw_nix_config_tests
  _run_openclaw_live_service_tests

  echo "=== All Tests Complete ==="
}

_parse_arguments() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --ci) ciMode=true; shift ;;
      --coverage) coverageMode=true; shift ;;
      --runtime) runtimeMode=true; shift ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done
}

_run_skill_frontmatter_validation() {
  echo "--- Skill Frontmatter Validation ---"
  "$SCRIPT_DIR/validate-skill-frontmatter.sh" "$SCRIPT_DIR/../agents/skills"
  echo ""
}

_run_bin_script_tests() {
  if [[ "$coverageMode" == "true" ]]; then
    _run_bin_script_tests_with_coverage
  elif command -v bats &>/dev/null; then
    echo "--- Bin Script Tests (bats) ---"
    bats "$SCRIPT_DIR/bin-scripts/"
  elif [[ "$ciMode" == "true" ]]; then
    echo "SKIP: bats not installed"
  else
    echo "WARN: bats not installed, skipping bin script tests"
    echo "      Install with: nix shell nixpkgs#bats"
  fi
}

_run_bin_script_tests_with_coverage() {
  if command -v kcov &>/dev/null && command -v bats &>/dev/null; then
    echo "--- Bin Script Tests with Coverage ---"
    "$SCRIPT_DIR/bash-coverage.sh"
  else
    echo "WARN: kcov or bats not installed, skipping coverage"
    echo "      Install with: nix shell nixpkgs#kcov nixpkgs#bats"
  fi
}

_run_home_manager_module_tests() {
  if command -v nix &>/dev/null && command -v bats &>/dev/null; then
    echo "--- Home Manager Module Tests (bats + nix eval) ---"
    bats "$SCRIPT_DIR/nix-modules/home-manager.bats"
  elif [[ "$ciMode" == "true" ]]; then
    echo "SKIP: nix or bats not installed for home manager module tests"
  else
    echo "WARN: nix or bats not installed, skipping home manager module tests"
  fi
  echo ""
}

_run_openclaw_nix_config_tests() {
  if command -v nix &>/dev/null && command -v bats &>/dev/null; then
    echo "--- OpenClaw Nix Config Tests (bats + nix eval) ---"
    bats "$SCRIPT_DIR/openclaw/nix-config.bats"
  elif [[ "$ciMode" == "true" ]]; then
    echo "SKIP: nix or bats not installed for openclaw nix config tests"
  else
    echo "WARN: nix or bats not installed, skipping openclaw nix config tests"
  fi
  echo ""
}

_run_openclaw_live_service_tests() {
  [[ "$runtimeMode" != "true" ]] && return 0

  if command -v bats &>/dev/null; then
    echo "--- OpenClaw Live Service Tests (bats) ---"
    bats "$SCRIPT_DIR/openclaw/live-services.bats"
  else
    echo "WARN: bats not installed, skipping live service tests"
  fi
  echo ""
}

main "$@"
