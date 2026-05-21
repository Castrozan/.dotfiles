#!/usr/bin/env bash
# Seed a project-manager agent's workspace under an existing project tree.
#
# Arguments:
#   $1  absolute path of the project the PM owns (e.g. ~/repo/coates-pm)
#
# Behavior:
#   - Ensures <projectDir>/.pm/ exists.
#   - Seeds <projectDir>/.pm/HEARTBEAT.md with the standard "No active work"
#     placeholder if absent. PM detects first session by reading this file.
#   - Appends .pm/ and memory/ to <projectDir>/.gitignore (idempotent) so
#     agent state and memory files never get committed to the project repo.
#
# Idempotent. Safe to run on every home-manager activation.

set -euo pipefail

readonly PROJECT_DIRECTORY="${1:?usage: seed-pm-workspace <project-directory>}"
readonly PM_STATE_DIRECTORY="${PROJECT_DIRECTORY}/.pm"
readonly PM_HEARTBEAT_PATH="${PM_STATE_DIRECTORY}/HEARTBEAT.md"
readonly PROJECT_GITIGNORE_PATH="${PROJECT_DIRECTORY}/.gitignore"

_seed_pm_state_directory() {
	mkdir -p "${PM_STATE_DIRECTORY}"
	if [ ! -f "${PM_HEARTBEAT_PATH}" ]; then
		printf '# Heartbeat\n\nNo active work.\n' >"${PM_HEARTBEAT_PATH}"
	fi
}

_ensure_pattern_in_gitignore() {
	local pattern="$1"
	if [ ! -f "${PROJECT_GITIGNORE_PATH}" ]; then
		printf '%s\n' "${pattern}" >"${PROJECT_GITIGNORE_PATH}"
		return
	fi
	if ! grep -Fxq "${pattern}" "${PROJECT_GITIGNORE_PATH}"; then
		printf '%s\n' "${pattern}" >>"${PROJECT_GITIGNORE_PATH}"
	fi
}

_ensure_pm_artifacts_gitignored() {
	if [ ! -d "${PROJECT_DIRECTORY}" ]; then
		return
	fi
	_ensure_pattern_in_gitignore ".pm/"
	_ensure_pattern_in_gitignore "memory/"
}

main() {
	if [ ! -d "${PROJECT_DIRECTORY}" ]; then
		echo "[pm-seed] project dir ${PROJECT_DIRECTORY} does not exist; skipping seed" >&2
		return 0
	fi
	_seed_pm_state_directory
	_ensure_pm_artifacts_gitignored
}

main "$@"
