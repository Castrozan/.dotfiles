#!/usr/bin/env sh

commit_message_file="$1"

staged_files=$(git diff --cached --name-only)

scope=$(printf '%s\n' "$staged_files" |
	grep -m1 -E '^(hosts/[^/]+/|home/hosts/(linux|darwin)/[^/]+(\.nix|/))' |
	sed -E -e 's#^hosts/([^/]+)/.*#\1#' -e 's#^home/hosts/(linux|darwin)/([^/.]+)(\.nix|/.*)#\2#')

[ -z "$scope" ] && exit 0

scope_prefix="($scope)"

subject=$(head -n 1 "$commit_message_file")
body=$(tail -n +2 "$commit_message_file")

case "$subject" in
*"${scope_prefix}:"*) exit 0 ;;
esac

prefixed_subject=$(printf '%s' "$subject" | sed -E "s/^([^:]+):/\\1${scope_prefix}:/")

{
	printf '%s\n' "$prefixed_subject"
	printf '%s' "$body"
} >"$commit_message_file"

exit 0
