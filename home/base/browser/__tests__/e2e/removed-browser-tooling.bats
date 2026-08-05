#!/usr/bin/env bats
bats_require_minimum_version 1.5.0

readonly REPOSITORY_ROOT="$BATS_TEST_DIRNAME/../../../../.."
readonly BROWSER_MODULE_DIRECTORY="$BATS_TEST_DIRNAME/../.."

@test "pw CLI is no longer in PATH" {
	run which pw
	[[ "$status" -ne 0 ]]
}

@test "agent-browser package files are removed" {
	[[ ! -f "$BROWSER_MODULE_DIRECTORY/agent-browser-package.nix" ]]
	[[ ! -f "$BROWSER_MODULE_DIRECTORY/scripts.nix" ]]
}

@test "deleted pw and playwright files do not exist" {
	[[ ! -f "$REPOSITORY_ROOT/agent-harness/agent-instructions/skills/browser/scripts/pw.sh" ]]
	[[ ! -f "$REPOSITORY_ROOT/agent-harness/agent-instructions/skills/browser/scripts/pw.js" ]]
	[[ ! -f "$REPOSITORY_ROOT/agent-harness/agent-instructions/skills/browser/scripts/pw-daemon.js" ]]
	[[ ! -f "$REPOSITORY_ROOT/agent-harness/agent-instructions/skills/browser/default.nix" ]]
	[[ ! -f "$REPOSITORY_ROOT/agent-harness/agent-instructions/skills/ponto/scripts/playwright-resolver.js" ]]
	[[ ! -f "$REPOSITORY_ROOT/home/base/playwright.nix" ]]
}

@test "cdp-browser module removed with the CDP scripts stays removed" {
	[[ ! -f "$REPOSITORY_ROOT/agent-harness/agent-instructions/skills/ponto/scripts/cdp-browser.js" ]]
}

@test "no stale PW_PORT or playwright-resolver references" {
	run ! grep -r --include='*.js' --include='*.sh' --include='*.nix' \
		'PW_PORT' "$REPOSITORY_ROOT/agents" "$REPOSITORY_ROOT/home"
	run ! grep -r --include='*.js' --include='*.sh' --include='*.nix' \
		'playwright-resolver' "$REPOSITORY_ROOT/agents" "$REPOSITORY_ROOT/home"
}
