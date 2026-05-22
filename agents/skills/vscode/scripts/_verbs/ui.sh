# shellcheck shell=bash
# UI verbs: probe-chat-dom, dismiss-modals, command-by-title, click, type,
# type-focused, screenshot, snapshot. Sourced from `scripts/vscode`.

_verb_probe_chat_dom() {
	_assert_running
	_python_helper "probe_chat_dom"
}

_verb_dismiss_modals() {
	_assert_running
	local presses="${1:-3}"
	if [[ ! "$presses" =~ ^[1-9][0-9]*$ ]]; then
		echo "dismiss-modals: presses must be a positive integer, got '${presses}'" >&2
		exit 1
	fi
	_python_helper "dismiss_modals" --presses "$presses"
}

_verb_command_by_title() {
	_assert_running
	local command_title="${1:-}"
	[[ -z "$command_title" ]] && {
		echo "Usage: vscode command-by-title <command-title>" >&2
		echo "  Pass the user-visible title (locale-dependent), not the internal id." >&2
		echo "  Example: vscode command-by-title \"Preferences: Open Settings (UI)\"" >&2
		exit 1
	}
	_python_helper "command_by_title" --command-title "$command_title"
}

_verb_click() {
	_assert_running
	local selector="${1:-}"
	[[ -z "$selector" ]] && {
		echo "Usage: vscode click <css-selector>" >&2
		exit 1
	}
	_python_helper "click" --selector "$selector"
}

_verb_type() {
	_assert_running
	local selector="${1:-}"
	local text="${2:-}"
	[[ -z "$selector" || -z "$text" ]] && {
		echo "Usage: vscode type <css-selector> <text>" >&2
		exit 1
	}
	_python_helper "type" --selector "$selector" --text "$text"
}

_verb_type_focused() {
	_assert_running
	local text="${1:-}"
	[[ -z "$text" ]] && {
		echo "Usage: vscode type-focused <text>" >&2
		echo "  Sends text to whatever element currently has focus, via CDP" >&2
		echo "  Input.insertText. Required when the target is a Monaco editor" >&2
		echo "  widget (e.g., the Extensions sidebar search input, the workbench" >&2
		echo "  Search view input) — those are not plain HTMLInputElements so" >&2
		echo "  document.querySelector + .focus() + execCommand do not work." >&2
		echo "  Use after a 'Focus on ... View' palette command." >&2
		exit 1
	}
	uv run --quiet --script "$LIB_DIR/cdp_type_focused.py" --port "$CDP_PORT" --text "$text"
}

_verb_screenshot() {
	_assert_running
	local out_path=""
	local full="false"
	while (("$#")); do
		case "$1" in
		--out)
			out_path="$2"
			shift 2
			;;
		--full)
			full="true"
			shift
			;;
		*) shift ;;
		esac
	done
	[[ -z "$out_path" ]] && out_path="/tmp/vscode-cdp-${CDP_PORT}-screenshot.png"
	_python_helper "screenshot" --out "$out_path" --full "$full"
	echo "$out_path"
}

_verb_snapshot() {
	_assert_running
	_python_helper "snapshot"
}
