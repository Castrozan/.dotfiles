# shellcheck shell=bash

_upstream_fetch_marker_file_for_repository() {
	local repository_directory="$1"
	local temporary_directory hashed_directory
	temporary_directory="${TMPDIR:-/tmp}"
	hashed_directory=$(printf "%s" "$repository_directory" | shasum | cut -d' ' -f1)
	printf "%s/claude-statusline-upstream-fetch-%s" "${temporary_directory%/}" "$hashed_directory"
}

_seconds_since_last_upstream_fetch_attempt() {
	local marker_file="$1"
	local last_attempt_epoch
	last_attempt_epoch=$(cat "$marker_file" 2>/dev/null) || return 1
	[[ "$last_attempt_epoch" =~ ^[0-9]+$ ]] || return 1
	printf "%s" "$(($(date +%s) - last_attempt_epoch))"
}

_terminate_upstream_fetch_after_timeout() {
	local fetch_process_id="$1"
	sleep "$GIT_UPSTREAM_FETCH_TIMEOUT_SECONDS"
	kill "$fetch_process_id" 2>/dev/null || true
}

_fetch_upstream_tracking_ref_under_watchdog() {
	local repository_directory="$1" remote_name="$2" remote_branch_ref="$3"

	GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=5" \
		git -C "$repository_directory" fetch --quiet "$remote_name" "$remote_branch_ref" &
	local fetch_process_id=$!

	_terminate_upstream_fetch_after_timeout "$fetch_process_id" &
	local watchdog_process_id=$!

	wait "$fetch_process_id" 2>/dev/null || true
	kill "$watchdog_process_id" 2>/dev/null || true
}

_refresh_upstream_tracking_ref_in_background() {
	local repository_directory="$1" branch_name="$2"

	local remote_name remote_branch_ref
	remote_name=$(git --no-optional-locks config --get "branch.${branch_name}.remote" 2>/dev/null) || return 0
	remote_branch_ref=$(git --no-optional-locks config --get "branch.${branch_name}.merge" 2>/dev/null) || return 0
	if [ -z "$remote_name" ] || [ -z "$remote_branch_ref" ] || [ "$remote_name" = "." ]; then
		return 0
	fi

	local marker_file seconds_since_last_attempt
	marker_file=$(_upstream_fetch_marker_file_for_repository "$repository_directory")
	if seconds_since_last_attempt=$(_seconds_since_last_upstream_fetch_attempt "$marker_file"); then
		if [ "$seconds_since_last_attempt" -lt "$GIT_UPSTREAM_FETCH_INTERVAL_SECONDS" ]; then
			return 0
		fi
	fi
	date +%s >"$marker_file" 2>/dev/null || return 0

	_fetch_upstream_tracking_ref_under_watchdog \
		"$repository_directory" "$remote_name" "$remote_branch_ref" >/dev/null 2>&1 &
}

_build_git_segment_from_repo_directory() {
	local repository_directory="$1"

	cd "$repository_directory" || return 0

	local branch_name
	branch_name=$(git --no-optional-locks branch --show-current 2>/dev/null) || return 0
	[ -z "$branch_name" ] && return 0

	local dirty_marker=""
	if ! git --no-optional-locks diff --quiet 2>/dev/null || ! git --no-optional-locks diff --cached --quiet 2>/dev/null; then
		dirty_marker="*"
	fi

	local upstream_tracking_ref
	upstream_tracking_ref=$(git --no-optional-locks rev-parse --abbrev-ref "@{upstream}" 2>/dev/null) || upstream_tracking_ref=""

	local ahead_behind_counts=""
	if [ -n "$upstream_tracking_ref" ]; then
		local ahead_count behind_count
		ahead_count=$(git --no-optional-locks rev-list --count "@{upstream}..HEAD" 2>/dev/null) || ahead_count=0
		behind_count=$(git --no-optional-locks rev-list --count "HEAD..@{upstream}" 2>/dev/null) || behind_count=0

		[ "$ahead_count" -gt 0 ] && ahead_behind_counts="${ahead_behind_counts}↑${ahead_count}"
		[ "$behind_count" -gt 0 ] && ahead_behind_counts="${ahead_behind_counts}↓${behind_count}"
		[ -n "$ahead_behind_counts" ] && ahead_behind_counts=" ${ahead_behind_counts}"

		_refresh_upstream_tracking_ref_in_background "$repository_directory" "$branch_name"
	fi

	printf "${COLOR_GREEN}%s%s%s${COLOR_RESET}" "$branch_name" "$dirty_marker" "$ahead_behind_counts"
}
