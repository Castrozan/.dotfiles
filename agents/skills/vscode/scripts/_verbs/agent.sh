# shellcheck shell=bash
# Agent (Claude Code chat panel) verb. Sourced from `scripts/vscode`.

_verb_agent() {
	_assert_running
	local subverb="${1:-}"
	[[ -z "$subverb" ]] && {
		echo "Usage: vscode agent <send|state|read|wait-idle|new|transcript|history> [...]" >&2
		exit 1
	}
	shift
	# Subverbs consume their positionals differently; map them onto the named
	# flags the Python helper expects.
	case "$subverb" in
	send)
		local message="${1:-}"
		[[ -z "$message" ]] && {
			echo "Usage: vscode agent send <message>" >&2
			exit 1
		}
		_python_helper "agent" --subverb "send" --message "$message"
		;;
	state)
		_python_helper "agent" --subverb "state"
		;;
	read)
		_python_helper "agent" --subverb "read"
		;;
	wait-idle)
		local timeout="1800"
		local poll="20"
		while (("$#")); do
			case "$1" in
			--timeout)
				timeout="$2"
				shift 2
				;;
			--poll)
				poll="$2"
				shift 2
				;;
			*) shift ;;
			esac
		done
		_python_helper "agent" --subverb "wait-idle" --timeout "$timeout" --poll "$poll"
		;;
	transcript | history | new)
		_python_helper "agent" --subverb "$subverb"
		;;
	*)
		echo "Unknown agent subverb: $subverb (use one of: send, state, read, wait-idle, new, transcript, history)" >&2
		exit 1
		;;
	esac
}
