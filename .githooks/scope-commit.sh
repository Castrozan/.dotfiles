#!/usr/bin/env sh

commit_message_file="$1"

staged_files=$(git diff --cached --name-only)

scope=$(printf '%s\n' "$staged_files" |
	grep -m1 -E '^(hosts/[^/]+/|hosts/[^/.]+-configuration\.nix$|home/hosts/(linux|darwin)/[^/]+(\.nix|/)|\.githooks/)' |
	sed -E -e 's#^hosts/([^/]+)/.*#\1#' -e 's#^hosts/([^/.]+)-configuration\.nix$#\1#' -e 's#^home/hosts/(linux|darwin)/([^/.]+)(\.nix|/.*)#\2#' -e 's#^\.githooks/.*#githooks#')

subject=$(head -n 1 "$commit_message_file")
body=$(tail -n +2 "$commit_message_file")

case "$subject" in
"Merge "* | "Revert "* | "fixup! "* | "squash! "*) exit 0 ;;
esac

if ! printf '%s' "$subject" | grep -E -q '^[a-z]+(\([a-z0-9-]+\))*: '; then
	printf 'commit-msg: subject must be "type(scope): subject", got:\n  %s\n' "$subject" >&2
	exit 1
fi

[ -z "$scope" ] && exit 0

case "$subject" in
*"($scope):"*) exit 0 ;;
esac

prefixed_subject=$(printf '%s' "$subject" | sed -E "s/^([^:]+):/\\1($scope):/")

{
	printf '%s\n' "$prefixed_subject"
	printf '%s' "$body"
} >"$commit_message_file"

exit 0
