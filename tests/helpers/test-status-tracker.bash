#!/usr/bin/env bash

_test_status_tracking_directory() {
  echo "${BATS_TEST_DIRNAME}/.test-status"
}

_test_status_failure_marker() {
  echo "$(_test_status_tracking_directory)/.failures"
}

_test_status_count_file() {
  echo "$(_test_status_tracking_directory)/.count"
}

_initialize_test_status_tracking() {
  local trackingDir
  trackingDir=$(_test_status_tracking_directory)
  mkdir -p "$trackingDir"
  rm -f "$(_test_status_failure_marker)" "$(_test_status_count_file)"
  echo 0 > "$(_test_status_count_file)"
}

_record_test_failure_if_any() {
  local countFile
  countFile=$(_test_status_count_file)
  local currentCount
  currentCount=$(cat "$countFile" 2>/dev/null || echo 0)
  echo $(( currentCount + 1 )) > "$countFile"

  if [[ "${BATS_TEST_COMPLETED:-}" != "1" ]]; then
    touch "$(_test_status_failure_marker)"
  fi
}

_write_passing_status_if_all_passed() {
  local trackingDir
  trackingDir=$(_test_status_tracking_directory)
  local statusFile="${trackingDir}/$(basename "${BATS_TEST_FILENAME}" .bats).last-pass"
  local testCount
  testCount=$(cat "$(_test_status_count_file)" 2>/dev/null || echo "?")

  if [[ ! -f "$(_test_status_failure_marker)" ]]; then
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

  rm -f "$(_test_status_failure_marker)" "$(_test_status_count_file)"
}
