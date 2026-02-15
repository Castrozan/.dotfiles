#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

main() {
  local selectedMode="quick"

  _parse_arguments "$@"

  echo "=== Running Tests (${selectedMode}) ==="
  echo ""

  case "$selectedMode" in
    quick)    _run_quick_tier ;;
    nix)      _run_quick_tier; _run_nix_tier ;;
    docker)   _run_docker_tier ;;
    runtime)  _run_runtime_tier ;;
    all)      _run_quick_tier; _run_nix_tier; _run_docker_tier ;;
    coverage) _run_coverage_tier ;;
    ci)       _run_ci_tier ;;
  esac

  echo "=== All Tests Complete ==="
}

_parse_arguments() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --quick)    selectedMode="quick"; shift ;;
      --nix)      selectedMode="nix"; shift ;;
      --docker)   selectedMode="docker"; shift ;;
      --runtime)  selectedMode="runtime"; shift ;;
      --all)      selectedMode="all"; shift ;;
      --coverage) selectedMode="coverage"; shift ;;
      --ci)       selectedMode="ci"; shift ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done
}

_run_quick_tier() {
  _run_skill_frontmatter_validation
  _run_quick_bats_tests
}

_run_nix_tier() {
  _run_home_manager_module_tests
  _run_openclaw_nix_config_tests
}

_run_docker_tier() {
  _run_docker_integration_tests
}

_run_runtime_tier() {
  _run_openclaw_live_service_tests
}

_run_coverage_tier() {
  _run_skill_frontmatter_validation
  _run_bats_with_coverage
}

_run_ci_tier() {
  _run_skill_frontmatter_validation
  _run_quick_bats_tests_ci
}

_run_skill_frontmatter_validation() {
  echo "--- Skill Frontmatter Validation ---"
  "$SCRIPT_DIR/validate-skill-frontmatter.sh" "$SCRIPT_DIR/../agents/skills"
  echo ""
}

_collect_quick_bats_test_files() {
  local testFiles=()
  for testFile in "$SCRIPT_DIR"/bin-scripts/*.bats; do
    [[ "$(basename "$testFile")" == *-docker.bats ]] && continue
    testFiles+=("$testFile")
  done
  printf '%s\n' "${testFiles[@]}"
}

_run_quick_bats_tests() {
  if ! command -v bats &>/dev/null; then
    echo "WARN: bats not installed, skipping bin script tests" >&2
    echo "      Install with: nix shell nixpkgs#bats" >&2
    return 0
  fi

  echo "--- Bin Script Tests (quick) ---"
  local testFiles
  testFiles=$(_collect_quick_bats_test_files)
  bats $testFiles
  echo ""
}

_run_quick_bats_tests_ci() {
  if ! command -v bats &>/dev/null; then
    echo "SKIP: bats not installed"
    return 0
  fi

  echo "--- Bin Script Tests (ci) ---"
  local testFiles
  testFiles=$(_collect_quick_bats_test_files)
  bats $testFiles
  echo ""
}

_run_home_manager_module_tests() {
  if ! command -v nix &>/dev/null; then
    echo "WARN: nix not installed, skipping home manager module tests" >&2
    return 0
  fi
  if ! command -v bats &>/dev/null; then
    echo "WARN: bats not installed, skipping home manager module tests" >&2
    return 0
  fi

  echo "--- Home Manager Module Tests (nix eval) ---"
  bats "$SCRIPT_DIR/nix-modules/home-manager.bats"
  echo ""
}

_run_openclaw_nix_config_tests() {
  if ! command -v nix &>/dev/null; then
    echo "WARN: nix not installed, skipping openclaw nix config tests" >&2
    return 0
  fi
  if ! command -v bats &>/dev/null; then
    echo "WARN: bats not installed, skipping openclaw nix config tests" >&2
    return 0
  fi

  echo "--- OpenClaw Nix Config Tests (nix eval) ---"
  bats "$SCRIPT_DIR/openclaw/nix-config.bats"
  echo ""
}

_run_docker_integration_tests() {
  if ! command -v docker &>/dev/null; then
    echo "WARN: docker not installed, skipping docker integration tests" >&2
    return 0
  fi
  if ! command -v bats &>/dev/null; then
    echo "WARN: bats not installed, skipping docker integration tests" >&2
    return 0
  fi

  echo "--- Docker Integration Tests ---"
  local dockerTestFiles=()
  for testFile in "$SCRIPT_DIR"/bin-scripts/*-docker.bats; do
    [[ -f "$testFile" ]] && dockerTestFiles+=("$testFile")
  done

  if [[ ${#dockerTestFiles[@]} -eq 0 ]]; then
    echo "No docker test files found"
    return 0
  fi

  bats "${dockerTestFiles[@]}"
  echo ""
}

_run_openclaw_live_service_tests() {
  if ! command -v bats &>/dev/null; then
    echo "WARN: bats not installed, skipping live service tests" >&2
    return 0
  fi

  echo "--- OpenClaw Live Service Tests ---"
  bats "$SCRIPT_DIR/openclaw/live-services.bats"
  echo ""
}

_run_bats_with_coverage() {
  if ! command -v kcov &>/dev/null || ! command -v bats &>/dev/null; then
    echo "WARN: kcov or bats not installed, skipping coverage" >&2
    echo "      Install with: nix shell nixpkgs#kcov nixpkgs#bats" >&2
    return 0
  fi

  echo "--- Bin Script Tests with Coverage ---"
  "$SCRIPT_DIR/bash-coverage.sh"
  echo ""
}

main "$@"
