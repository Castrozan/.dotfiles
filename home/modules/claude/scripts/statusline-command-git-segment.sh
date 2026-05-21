# shellcheck shell=bash

_git_cache_file_for_directory() {
	local directory="$1"
	local hashed_directory
	hashed_directory=$(echo "$directory" | shasum | cut -d' ' -f1)
	echo "/tmp/claude-statusline-git-${hashed_directory}"
}

_repo_has_enough_files_to_benefit_from_caching() {
	local directory="$1"
	local tracked_file_count
	tracked_file_count=$(git -C "$directory" --no-optional-locks ls-files 2>/dev/null | wc -l) || return 1
	[ "$tracked_file_count" -ge "$GIT_CACHE_MIN_TRACKED_FILES_FOR_CACHING" ]
}

_git_cache_is_still_valid() {
	local cache_file="$1"
	[ -f "$cache_file" ] || return 1
	local cache_age_seconds
	cache_age_seconds=$(($(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || echo 0)))
	[ "$cache_age_seconds" -lt "$GIT_CACHE_TTL_SECONDS" ]
}

_build_git_segment_from_repo_directory() {
	local repository_directory="$1"

	cd "$repository_directory" || return 0

	local cache_file
	cache_file=$(_git_cache_file_for_directory "$repository_directory")

	if _repo_has_enough_files_to_benefit_from_caching "$repository_directory" && _git_cache_is_still_valid "$cache_file"; then
		cat "$cache_file"
		return 0
	fi

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
	fi

	local git_segment
	git_segment=$(printf "${COLOR_GREEN}%s%s%s${COLOR_RESET}" "$branch_name" "$dirty_marker" "$ahead_behind_counts")

	if _repo_has_enough_files_to_benefit_from_caching "$repository_directory"; then
		echo "$git_segment" >"$cache_file"
	fi

	printf "%s" "$git_segment"
}
