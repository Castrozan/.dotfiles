# shellcheck shell=bash
# Lifecycle verbs: launch, status, kill, wait-ready, reload-window, cdp-pages.
# Sourced from `scripts/vscode`. Relies on globals from the dispatcher:
# CDP_PORT, LIB_DIR, _is_running_on_port, _resolve_pid_listening_on_port,
# _assert_running, _python_helper.

_verb_launch() {
	local workspace_path="${1:-}"

	if _is_running_on_port; then
		echo "VS Code already exposing CDP on port ${CDP_PORT}; reusing instance."
		_verb_status
		return 0
	fi

	# The Nix-wrapped `code` binary always injects --remote-debugging-port and
	# --remote-allow-origins (see ~/.dotfiles/home/modules/editor/vscode/vscode.nix).
	# We pass no flags here — `code` uses Lucas's real ~/.config/Code profile so
	# logged-in Claude Code sessions, extensions, and settings are present.
	local -a args=()
	[[ -n "$workspace_path" ]] && args+=("$workspace_path")

	local stdout_log="/tmp/vscode-cdp-${CDP_PORT}.stdout.log"
	local stderr_log="/tmp/vscode-cdp-${CDP_PORT}.stderr.log"
	nohup code "${args[@]}" >"$stdout_log" 2>"$stderr_log" &
	disown || true

	local attempt=0
	while ((attempt < 30)); do
		if curl -sSf "http://localhost:${CDP_PORT}/json/version" >/dev/null 2>&1; then
			break
		fi
		sleep 0.5
		attempt=$((attempt + 1))
	done
	if ((attempt >= 30)); then
		echo "VS Code did not expose CDP on port ${CDP_PORT} within 15s. Check ${stderr_log}." >&2
		echo "(Confirm 'which code' resolves to the Nix-wrapped binary that injects --remote-debugging-port.)" >&2
		exit 1
	fi

	local resolved_pid
	resolved_pid="$(_resolve_pid_listening_on_port)"
	[[ -z "$resolved_pid" ]] && resolved_pid="?"
	echo "VS Code launched (pid=${resolved_pid}, port=${CDP_PORT}, profile=~/.config/Code)"
	_verb_status
}

_verb_status() {
	if ! _is_running_on_port; then
		echo "Not running on port ${CDP_PORT}."
		return 0
	fi
	local pid
	pid="$(_resolve_pid_listening_on_port)"
	[[ -z "$pid" ]] && pid="?"
	echo "Running: pid=${pid} port=${CDP_PORT}"
	echo "Pages:"
	curl -sS "http://localhost:${CDP_PORT}/json" | _python_helper "format_pages"
}

_verb_kill() {
	if ! _is_running_on_port; then
		echo "Not running on port ${CDP_PORT}."
		return 0
	fi
	echo "Closing VS Code on port ${CDP_PORT}..."
	# Earlier versions routed kill through the Command Palette ("Quit" by
	# title). That made the kill verb depend on the editor locale — a
	# pt-BR install shows "Sair" — for no real gain. Direct signals
	# accomplish the same graceful shutdown without the title coupling.
	local pid
	pid="$(_resolve_pid_listening_on_port)"
	if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
		kill "$pid" 2>/dev/null || true
		sleep 1
		kill -9 "$pid" 2>/dev/null || true
	fi
	# NEVER touch the user-data-dir — it is the user's real ~/.config/Code.
	echo "Killed."
}

_verb_wait_ready() {
	local timeout_seconds=30
	while (("$#")); do
		case "$1" in
		--timeout)
			timeout_seconds="$2"
			shift 2
			;;
		*) shift ;;
		esac
	done
	local elapsed=0
	while ((elapsed < timeout_seconds)); do
		if _is_running_on_port; then
			# tiny grace period so the renderer page registers in CDP
			sleep 1
			return 0
		fi
		sleep 1
		elapsed=$((elapsed + 1))
	done
	echo "VS Code did not expose CDP on port ${CDP_PORT} within ${timeout_seconds}s." >&2
	exit 1
}

_verb_reload_window() {
	_assert_running
	# command-by-title is locale-dependent. The pt-BR title is
	# "Desenvolvedor: Recarregar Janela"; falling back to it keeps the verb
	# working on both en-US and pt-BR installs without forcing the caller to
	# care. CDP cannot reach the Extension Host, so there is no real
	# workbench.action.reloadWindow bridge — palette typing is the cheap path.
	if ! _python_helper "command_by_title" --command-title "Developer: Reload Window" >/dev/null 2>&1; then
		_python_helper "command_by_title" --command-title "Desenvolvedor: Recarregar Janela"
	fi
	_verb_wait_ready --timeout 60
}

_verb_cdp_pages() {
	_assert_running
	if [[ "${1:-}" == "--raw" ]]; then
		curl -sS "http://localhost:${CDP_PORT}/json"
		return 0
	fi
	curl -sS "http://localhost:${CDP_PORT}/json" | _python_helper "format_pages"
}
