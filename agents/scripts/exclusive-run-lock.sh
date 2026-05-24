#!/usr/bin/env bash

acquire_exclusive_run_lock_or_emit_retry_instructions() {
	local lockHumanName="$1"
	local typicalDurationSeconds="$2"
	local optionalInProgressLogPath="${3:-}"

	if [[ "${DOTFILES_BYPASS_EXCLUSIVE_RUN_LOCK:-0}" == "1" ]]; then
		return 0
	fi

	local lockDirectoryPath="/tmp/dotfiles-${lockHumanName}.lock.d"
	local lockOwnerMetadataPath="${lockDirectoryPath}/owner"

	if _try_create_lock_directory_atomically "$lockDirectoryPath"; then
		_write_lock_owner_metadata "$lockOwnerMetadataPath" "$lockHumanName" "$typicalDurationSeconds" "$optionalInProgressLogPath"
		_register_lock_release_trap "$lockDirectoryPath"
		return 0
	fi

	if _remove_lock_directory_if_owning_process_is_dead "$lockDirectoryPath" "$lockOwnerMetadataPath"; then
		if _try_create_lock_directory_atomically "$lockDirectoryPath"; then
			_write_lock_owner_metadata "$lockOwnerMetadataPath" "$lockHumanName" "$typicalDurationSeconds" "$optionalInProgressLogPath"
			_register_lock_release_trap "$lockDirectoryPath"
			return 0
		fi
	fi

	_emit_concurrent_run_contention_retry_instructions_to_stderr "$lockHumanName" "$lockOwnerMetadataPath"
	exit 99
}

_try_create_lock_directory_atomically() {
	local lockDirectoryPath="$1"
	mkdir "$lockDirectoryPath" 2>/dev/null
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
	} >"$lockOwnerMetadataPath"
}

_register_lock_release_trap() {
	local lockDirectoryPath="$1"
	DOTFILES_EXCLUSIVE_RUN_LOCK_DIRECTORY_TO_RELEASE_ON_EXIT="$lockDirectoryPath"
	trap _release_registered_exclusive_run_lock_on_exit EXIT
}

_release_registered_exclusive_run_lock_on_exit() {
	if [[ -n "${DOTFILES_EXCLUSIVE_RUN_LOCK_DIRECTORY_TO_RELEASE_ON_EXIT:-}" ]]; then
		rm -rf "$DOTFILES_EXCLUSIVE_RUN_LOCK_DIRECTORY_TO_RELEASE_ON_EXIT"
	fi
}

_remove_lock_directory_if_owning_process_is_dead() {
	local lockDirectoryPath="$1"
	local lockOwnerMetadataPath="$2"

	if [[ ! -f "$lockOwnerMetadataPath" ]]; then
		rm -rf "$lockDirectoryPath"
		return 0
	fi

	local owningProcessId
	owningProcessId=$(_read_lock_metadata_value "$lockOwnerMetadataPath" "pid")

	if [[ -z "$owningProcessId" ]] || ! kill -0 "$owningProcessId" 2>/dev/null; then
		rm -rf "$lockDirectoryPath"
		return 0
	fi
	return 1
}

_read_lock_metadata_value() {
	local lockOwnerMetadataPath="$1"
	local metadataKey="$2"
	grep "^${metadataKey}=" "$lockOwnerMetadataPath" 2>/dev/null | head -1 | cut -d= -f2- || true
}

_emit_concurrent_run_contention_retry_instructions_to_stderr() {
	local lockHumanName="$1"
	local lockOwnerMetadataPath="$2"

	local owningProcessId="unknown"
	local startedAtEpoch=0
	local typicalDurationSeconds=0
	local inProgressLogPath=""

	if [[ -f "$lockOwnerMetadataPath" ]]; then
		owningProcessId=$(_read_lock_metadata_value "$lockOwnerMetadataPath" "pid")
		startedAtEpoch=$(_read_lock_metadata_value "$lockOwnerMetadataPath" "started_epoch")
		typicalDurationSeconds=$(_read_lock_metadata_value "$lockOwnerMetadataPath" "typical_duration_seconds")
		inProgressLogPath=$(_read_lock_metadata_value "$lockOwnerMetadataPath" "log_path")
		[[ -z "$owningProcessId" ]] && owningProcessId="unknown"
		[[ -z "$startedAtEpoch" ]] && startedAtEpoch=0
		[[ -z "$typicalDurationSeconds" ]] && typicalDurationSeconds=0
	fi

	local currentEpoch
	currentEpoch=$(date +%s)
	local elapsedSeconds=$((currentEpoch - startedAtEpoch))
	local estimatedRemainingSeconds=$((typicalDurationSeconds - elapsedSeconds))
	if [[ $estimatedRemainingSeconds -lt 0 ]]; then
		estimatedRemainingSeconds=0
	fi
	local recommendedWaitSeconds=$((estimatedRemainingSeconds + 30))
	local startedAtHuman
	startedAtHuman=$(date -r "$startedAtEpoch" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "unknown")

	{
		echo "LOCKED_BY_CONCURRENT_RUN"
		echo "script:               ${lockHumanName}"
		echo "in_progress_pid:      ${owningProcessId}"
		echo "started_at:           ${startedAtHuman} (${elapsedSeconds}s ago)"
		echo "typical_duration:     ${typicalDurationSeconds}s"
		echo "estimated_remaining:  ~${estimatedRemainingSeconds}s"
		if [[ -n "$inProgressLogPath" ]]; then
			echo "in_progress_log:      ${inProgressLogPath}"
		fi
		echo ""
		echo "Contention from a parallel agent. Do not retry in a tight loop."
		echo "Wait for PID ${owningProcessId} to finish before re-executing '${lockHumanName}'."
		echo ""
		echo "Recommended wait: at least ${recommendedWaitSeconds}s."
		echo ""
		echo "If operating under Claude Code /loop, schedule a wakeup instead of busy-polling:"
		echo "  ScheduleWakeup(delaySeconds=${recommendedWaitSeconds}, reason=\"${lockHumanName} blocked by PID ${owningProcessId}; retry after parallel agent finishes\")"
	} >&2
}
