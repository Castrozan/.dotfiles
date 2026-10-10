#!/usr/bin/env bash

capture_exclusive_run_owner() {
	DOTFILES_EXCLUSIVE_RUN_OWNER="$(python3 "${BASH_SOURCE[0]%/*}/exclusive_run_owner.py" "$$")" || return 1
	export DOTFILES_EXCLUSIVE_RUN_OWNER
}

acquire_exclusive_run_lock_or_emit_retry_instructions() {
	local lockHumanName="$1"
	local typicalDurationSeconds="$2"
	local optionalInProgressLogPath="${3:-}"

	if [[ ! "$lockHumanName" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]*$ ]] || [[ ! "$typicalDurationSeconds" =~ ^[0-9]{1,9}$ ]]; then
		echo "error: invalid exclusive run lock name or duration" >&2
		exit 1
	fi

	local lockOwnerMetadataPath="/tmp/dotfiles-${lockHumanName}.lock"
	local lockDriverPath="${BASH_SOURCE[0]%/*}/exclusive_run_lock.py"
	if ! python3 "$lockDriverPath" prepare "$lockOwnerMetadataPath"; then
		exit 1
	fi
	if ! exec {DOTFILES_EXCLUSIVE_RUN_LOCK_FILE_DESCRIPTOR}<"$lockOwnerMetadataPath"; then
		echo "error: cannot open exclusive run lock" >&2
		exit 1
	fi

	local acquisitionStatus=0
	python3 "$lockDriverPath" acquire "$lockOwnerMetadataPath" "$DOTFILES_EXCLUSIVE_RUN_LOCK_FILE_DESCRIPTOR" || acquisitionStatus=$?
	if [[ "$acquisitionStatus" -ne 0 ]]; then
		exec {DOTFILES_EXCLUSIVE_RUN_LOCK_FILE_DESCRIPTOR}<&-
		if [[ "$acquisitionStatus" -eq 99 ]]; then
			_emit_concurrent_run_contention_retry_instructions_to_stderr "$lockHumanName" "$lockOwnerMetadataPath"
		fi
		exit "$acquisitionStatus"
	fi
	if ! _write_lock_owner_metadata "$lockOwnerMetadataPath" "$lockHumanName" "$typicalDurationSeconds" "$optionalInProgressLogPath"; then
		exit 1
	fi
}

_write_lock_owner_metadata() {
	local lockOwnerMetadataPath="$1"
	local lockHumanName="$2"
	local typicalDurationSeconds="$3"
	local optionalInProgressLogPath="$4"

	{
		echo "pid=$$"
		echo "started_epoch=$(date +%s)"
		echo "script=${lockHumanName}"
		echo "typical_duration_seconds=${typicalDurationSeconds}"
		echo "log_path=${optionalInProgressLogPath}"
	} | python3 "${BASH_SOURCE[0]%/*}/exclusive_run_lock.py" write "$lockOwnerMetadataPath" "$DOTFILES_EXCLUSIVE_RUN_LOCK_FILE_DESCRIPTOR"
}

_emit_concurrent_run_contention_retry_instructions_to_stderr() {
	python3 "${BASH_SOURCE[0]%/*}/exclusive_run_diagnostics.py" "$1" "$2"
}
