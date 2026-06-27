set -eu

tmux_socket_name="$1"
tmux_session_name="$2"
tmux_configuration_path="$3"

tmux_for_persistent_session() {
	tmux -L "$tmux_socket_name" -f "$tmux_configuration_path" "$@"
}

if ! tmux_for_persistent_session has-session -t "$tmux_session_name" 2>/dev/null; then
	tmux_for_persistent_session new-session -d -s "$tmux_session_name" -x 120 -y 32 \
		"$JARVIS_PERSISTENT_SESSION_COMMAND"
fi

while tmux_for_persistent_session has-session -t "$tmux_session_name" 2>/dev/null; do
	sleep 5
done
