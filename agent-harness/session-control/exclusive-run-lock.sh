#!/usr/bin/env bash

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

_read_lock_metadata_value() {
	local lockOwnerMetadataPath="$1"
	local metadataKey="$2"
	grep "^${metadataKey}=" "$lockOwnerMetadataPath" 2>/dev/null | head -1 | cut -d= -f2- || true
}

_format_epoch_as_local_timestamp() {
	local epochSeconds="$1"
	date -d "@${epochSeconds}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null && return 0
	date -r "$epochSeconds" '+%Y-%m-%d %H:%M:%S' 2>/dev/null && return 0
	echo "unknown"
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
		[[ "$owningProcessId" =~ ^[1-9][0-9]{0,9}$ ]] || owningProcessId="unknown"
		[[ "$startedAtEpoch" =~ ^[0-9]{1,10}$ ]] || startedAtEpoch=0
		[[ "$typicalDurationSeconds" =~ ^[0-9]{1,9}$ ]] || typicalDurationSeconds=0
	fi
	startedAtEpoch=$((10#$startedAtEpoch))
	typicalDurationSeconds=$((10#$typicalDurationSeconds))

	local currentEpoch
	currentEpoch=$(date +%s)
	local elapsedSeconds=$((currentEpoch - startedAtEpoch))
	[[ "$elapsedSeconds" -lt 0 ]] && elapsedSeconds=0
	local estimatedRemainingSeconds=$((typicalDurationSeconds - elapsedSeconds))
	if [[ $estimatedRemainingSeconds -lt 0 ]]; then
		estimatedRemainingSeconds=0
	fi
	local recommendedWaitSeconds=$((estimatedRemainingSeconds + 30))
	local startedAtHuman
	startedAtHuman=$(_format_epoch_as_local_timestamp "$startedAtEpoch")

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
		echo "Wait for the owning run and its children to finish before re-executing '${lockHumanName}'."
		echo "The lock can remain held after metadata PID ${owningProcessId} exits."
		echo ""
		echo "Recommended wait: at least ${recommendedWaitSeconds}s."
		echo ""
		echo "If operating under Claude Code /loop, schedule a wakeup instead of busy-polling:"
		echo "  ScheduleWakeup(delaySeconds=${recommendedWaitSeconds}, reason=\"${lockHumanName} blocked by PID ${owningProcessId}; retry after parallel agent finishes\")"
	} >&2
}
