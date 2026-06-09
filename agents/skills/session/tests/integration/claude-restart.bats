#!/usr/bin/env bats

load '../../../../../tests/helpers/bash-script-assertions'

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "uses strict error handling" {
	assert_uses_strict_error_handling
}

@test "resolves the claude pid by walking ancestors via the shared helper" {
	assert_script_source_matches 'CLAUDE_PID=\$\(find-claude-ancestor-pid'
}

@test "fails safe when no claude ancestor is found" {
	assert_script_source_matches 'Safety check FAILED'
}

@test "defaults to a heads-up continuation so a bare restart resumes the agent into a turn" {
	assert_script_source_matches 'CONTINUATION_PROMPT="\$\{1:-\$DEFAULT_RESTART_HEADS_UP\}"'
}

@test "requires tmux environment variable" {
	assert_script_source_matches 'TMUX'
}

@test "extracts session id from --resume flag in process args" {
	assert_script_source_matches '--resume\[.*\]\+\(\[a-f0-9-\]'
}

@test "extracts session id from --session-id flag in process args" {
	assert_script_source_matches '--session-id\[.*\]\+\(\[a-f0-9-\]'
}

@test "derives project directory by replacing slashes with dashes" {
	assert_script_source_matches 'WORKING_DIRECTORY_SLASHES_REPLACED.*//\\//-'
}

@test "derives project directory by replacing dots with dashes" {
	assert_script_source_matches 'CLAUDE_PROJECT_DIR_NAME.*//\./-'
}

@test "finds most recent session file by modification time portably on darwin and linux" {
	assert_script_source_matches 'stat -f %m'
	assert_script_source_matches 'stat -c %Y'
}

@test "builds resume command with extracted session id" {
	assert_script_source_matches 'claude --resume \$EXTRACTED_SESSION_ID'
}

@test "falls back to --continue when no session id found" {
	assert_script_source_matches 'claude --continue'
}

@test "session file lookup checks correct directory structure" {
	assert_script_source_matches '\$HOME/\.claude/projects/\$CLAUDE_PROJECT_DIR_NAME'
}

@test "uses ps with wide output to avoid command line truncation" {
	assert_script_source_matches 'ps -ww -p'
}

@test "kills claude process after spawning background watcher" {
	assert_pattern_appears_before 'nohup' 'kill -TERM'
}

@test "checks pane existence in watcher loop to prevent orphan watchers" {
	assert_script_source_matches 'tmux display-message.*exit 0'
}

@test "kills child processes after claude death in watcher" {
	assert_script_source_matches 'pkill.*-P.*CLAUDE_PID'
}

@test "project dir path conversion handles dotfiles path correctly" {
	local test_path="/Users/lucas.zanoni/.dotfiles"
	local slashes_replaced="${test_path//\//-}"
	local dots_replaced="${slashes_replaced//./-}"
	[ "$dots_replaced" = "-Users-lucas-zanoni--dotfiles" ]
}

@test "project dir path conversion handles nested dot directories" {
	local test_path="/home/user/.config/.secrets"
	local slashes_replaced="${test_path//\//-}"
	local dots_replaced="${slashes_replaced//./-}"
	[ "$dots_replaced" = "-home-user--config--secrets" ]
}

@test "project dir path conversion handles path without dots" {
	local test_path="/home/user/projects/myapp"
	local slashes_replaced="${test_path//\//-}"
	local dots_replaced="${slashes_replaced//./-}"
	[ "$dots_replaced" = "-home-user-projects-myapp" ]
}
