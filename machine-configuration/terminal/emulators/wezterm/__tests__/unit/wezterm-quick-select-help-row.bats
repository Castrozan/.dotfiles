#!/usr/bin/env bats

readonly WEZTERM_DOMAIN="$BATS_TEST_DIRNAME/../.."
readonly WEZTERM_HOME_MANAGER_MODULE="$WEZTERM_DOMAIN/wezterm-home-manager.nix"
readonly PATCHED_WEZTERM_PACKAGE="$WEZTERM_DOMAIN/patched-wezterm.nix"
readonly QUICK_SELECT_HELP_ROW_PATCH="$WEZTERM_DOMAIN/wezterm-patches/hide-quick-select-help-row.patch"

@test "wezterm package customization stays behind the domain package adapter" {
	grep -Fq 'import ./patched-wezterm.nix' "$WEZTERM_HOME_MANAGER_MODULE"
	grep -Fq './wezterm-patches/hide-quick-select-help-row.patch' "$PATCHED_WEZTERM_PACKAGE"
}

@test "quick select patch removes the help row and restores the underlying cursor" {
	grep -Fq -- '-                                "Select: {}  (type highlighted prefix to {}, uppercase pastes, ESC to cancel)",' "$QUICK_SELECT_HELP_ROW_PATCH"
	grep -Fq -- '+        self.delegate.get_cursor_position()' "$QUICK_SELECT_HELP_ROW_PATCH"
}
