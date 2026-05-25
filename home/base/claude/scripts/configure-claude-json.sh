#!/usr/bin/env bash
# Configures $HOME/.claude.json safely from one activation pass:
# - creates with installMethod=native when missing
# - patches installMethod and accepts trust dialog for known paths when valid
# - preserves the file untouched on any read/write/parse failure (no clobber)
# - applies all edits in a single jq invocation, then atomic-mv via temp file
# Driven by TRUSTED_PARENT_DIRECTORIES, TRUSTED_DIRECTORIES, JQ_BIN env vars
# (newline-separated lists). Parent dirs trust each immediate child directory.

set -u

claude_json_path="$HOME/.claude.json"

if [ ! -f "$claude_json_path" ]; then
	echo '{"installMethod": "native"}' >"$claude_json_path"
	exit 0
fi

if ! "$JQ_BIN" -e . "$claude_json_path" >/dev/null 2>&1; then
	echo "WARNING: $claude_json_path is not valid JSON, leaving untouched" >&2
	exit 0
fi

trust_paths=()

while IFS= read -r parent_directory; do
	[ -z "$parent_directory" ] && continue
	[ -d "$parent_directory" ] || continue
	for child_directory in "$parent_directory"/*/; do
		child_directory="${child_directory%/}"
		[ -d "$child_directory" ] && trust_paths+=("$child_directory")
	done
done <<<"$TRUSTED_PARENT_DIRECTORIES"

while IFS= read -r trusted_directory; do
	[ -z "$trusted_directory" ] && continue
	trust_paths+=("$trusted_directory")
done <<<"$TRUSTED_DIRECTORIES"

jq_arguments=(--arg install_method native)
# shellcheck disable=SC2016 # $install_method is a jq variable, not a bash expansion
jq_filter='.installMethod = $install_method'
for path_index in "${!trust_paths[@]}"; do
	jq_arguments+=(--arg "path_${path_index}" "${trust_paths[$path_index]}")
	jq_filter+=" | .projects[\$path_${path_index}].hasTrustDialogAccepted = true"
done

temporary_path="${claude_json_path}.tmp.$$"
trap 'rm -f "$temporary_path"' EXIT

if ! "$JQ_BIN" "${jq_arguments[@]}" "$jq_filter" "$claude_json_path" >"$temporary_path"; then
	echo "ERROR: jq transformation failed, leaving $claude_json_path untouched" >&2
	exit 0
fi

if ! "$JQ_BIN" -e . "$temporary_path" >/dev/null 2>&1; then
	echo "ERROR: generated temp file is not valid JSON, leaving $claude_json_path untouched" >&2
	exit 0
fi

mv "$temporary_path" "$claude_json_path"
trap - EXIT
