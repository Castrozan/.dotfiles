#!/usr/bin/env bash

readonly STATUS_TRACKING_DIR="${BATS_TEST_DIRNAME}/.test-status"

_initialize_test_status_tracking() {
  mkdir -p "$STATUS_TRACKING_DIR"
  export BATS_SUITE_FAILURE_MARKER="${STATUS_TRACKING_DIR}/.failures-$$"
  export BATS_SUITE_TEST_COUNT_FILE="${STATUS_TRACKING_DIR}/.count-$$"
  rm -f "$BATS_SUITE_FAILURE_MARKER" "$BATS_SUITE_TEST_COUNT_FILE"
  echo 0 > "$BATS_SUITE_TEST_COUNT_FILE"
}

_record_test_failure_if_any() {
  local currentCount
  currentCount=$(cat "$BATS_SUITE_TEST_COUNT_FILE" 2>/dev/null || echo 0)
  echo $(( currentCount + 1 )) > "$BATS_SUITE_TEST_COUNT_FILE"

  if [[ "${status:-0}" -ne 0 ]]; then
    touch "$BATS_SUITE_FAILURE_MARKER"
  fi
}

_write_passing_status_if_all_passed() {
  local statusFile="${STATUS_TRACKING_DIR}/$(basename "${BATS_TEST_FILENAME}" .bats).last-pass"
  local testCount
  testCount=$(cat "$BATS_SUITE_TEST_COUNT_FILE" 2>/dev/null || echo "?")

  if [[ ! -f "$BATS_SUITE_FAILURE_MARKER" ]]; then
    local commitSha
    commitSha=$(git -C "${BATS_TEST_DIRNAME}" rev-parse --short HEAD 2>/dev/null || echo "unknown")
    local commitSubject
    commitSubject=$(git -C "${BATS_TEST_DIRNAME}" log -1 --format="%s" 2>/dev/null || echo "unknown")

    cat > "$statusFile" <<STATUSEOF
commit=${commitSha}
subject=${commitSubject}
passed_at=$(date -Iseconds)
tests=${testCount}
STATUSEOF
  fi

  rm -f "$BATS_SUITE_FAILURE_MARKER" "$BATS_SUITE_TEST_COUNT_FILE"
}
