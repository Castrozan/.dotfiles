#!/usr/bin/env sh

# commit-msg hook: auto‑prefix commit-subject with (<scope>)
# based on changes under users/<username>/ or hosts/<hostname>/

MSG_FILE="$1"

# get list of staged files
STAGED=$(git diff --cached --name-only)

# look for the first occurrence of users/<user>/ or hosts/<host>/
SCOPE_DIR=$(echo "$STAGED" | grep -m1 -E '^(users|hosts)/[^/]+/' | sed -E 's#^(users|hosts)/([^/]+)/.*#\2#')

# if no scope-dir found, skip
[ -z "$SCOPE_DIR" ] && exit 0

PREFIX="($SCOPE_DIR)"

# don't double‐up if it's already there
grep -qE "^[^:]+${PREFIX}:" "$MSG_FILE" && exit 0

# insert prefix before the first colon on the first line
if sed --version >/dev/null 2>&1; then
  # GNU sed
  sed -i -E "1 s/^([^:]+):/\\1${PREFIX}:/1" "$MSG_FILE"
else
  # BSD/macOS sed
  sed -i .bak -E "1 s/^([^:]+):/\\1${PREFIX}:/1" "$MSG_FILE" && rm -f "${MSG_FILE}.bak"
fi

exit 0
