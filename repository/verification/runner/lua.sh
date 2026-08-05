#!/usr/bin/env bash

_run_lua_unit_tests() {
	local luaTests
	luaTests=$(_discover_test_files "cross-platform" "*/__tests__/*_test.lua")

	if [[ -z "$luaTests" ]]; then
		return 0
	fi

	local luaInterpreter
	if command -v lua5.4 &>/dev/null; then
		luaInterpreter=(lua5.4)
	elif command -v lua &>/dev/null; then
		luaInterpreter=(lua)
	else
		luaInterpreter=(nix run nixpkgs#lua5_4 --)
	fi

	local isolatedWorkspaceStateFile
	isolatedWorkspaceStateFile="$(mktemp "${TMPDIR:-/tmp}/hammerspoon-workspace-state-test.XXXXXX")"
	export HAMMERSPOON_WORKSPACE_STATE_FILE="$isolatedWorkspaceStateFile"

	echo "--- Lua Unit Tests ---"
	local failCount=0
	for luaTest in $luaTests; do
		if ! "${luaInterpreter[@]}" "$luaTest"; then
			failCount=$((failCount + 1))
		fi
	done

	rm -f "$isolatedWorkspaceStateFile"
	unset HAMMERSPOON_WORKSPACE_STATE_FILE

	if [[ "$failCount" -gt 0 ]]; then
		echo "Lua tests: $failCount file(s) failed" >&2
		return 1
	fi
	echo ""
}
