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
# shellcheck disable=SC2016 # jq variables expand inside jq, not in bash
jq_filter='.installMethod = $install_method'
# Seed onboarding flags so a fresh .claude.json on a new machine does not
# show the first-run wizard on every `claude` launch. Each key uses //=
# (jq's "set if null") so a user's later changes are preserved.
jq_filter+=' | .theme //= "dark"'
jq_filter+=' | .hasCompletedOnboarding //= true'
jq_filter+=' | .hasOnboardedInPrevSession //= true'
jq_filter+=' | .themeOnboardingHasBeenSet //= true'
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
