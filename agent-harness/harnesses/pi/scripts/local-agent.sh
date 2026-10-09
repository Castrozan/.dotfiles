#!/usr/bin/env bash
export PI_CODING_AGENT_DIR=@profileDirectory@
export PI_AGENT_DIR="$PI_CODING_AGENT_DIR"
@systemctl@ --user start local-language-model.socket || exit "$?"
printf '%s\n' 'Preparing local Qwen. Cold startup can take up to 180 seconds.' >&2
@curl@ --fail --silent --show-error --max-time 180 @healthUrl@ >/dev/null || {
	startupStatus=$?
	printf '%s\n' 'Local Qwen did not become ready; the agent was not started.' >&2
	exit "$startupStatus"
}
printf '%s\n' 'Qwen is ready. It unloads after 5 minutes without connections; the next request reloads it.' >&2
exec @pi@ --offline --provider chise --model @modelId@ --thinking off "$@"
