#!/usr/bin/env bash

_run_lua_unit_tests() {
	local luaTests
	luaTests=$(find "$REPO_DIR/home" -path "*/tests/*_test.lua" -type f | sort)

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

	echo "--- Lua Unit Tests ---"
	local failCount=0
	for luaTest in $luaTests; do
		if ! "${luaInterpreter[@]}" "$luaTest"; then
			failCount=$((failCount + 1))
		fi
	done

	if [[ "$failCount" -gt 0 ]]; then
		echo "Lua tests: $failCount file(s) failed" >&2
		return 1
	fi
	echo ""
}
