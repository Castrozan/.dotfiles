#!/usr/bin/env sh
#
# commit-msg hook: auto‑prefix commit-subject with (<username>)
# based on changes under users/<username>/

MSG_FILE="$1"

# get list of staged files
STAGED=$(git diff --cached --name-only)

# look for the first occurrence of users/<user>/
USER_DIR=$(echo "$STAGED" | grep -m1 -E '^users/[^/]+/' | sed -E 's|users/([^/]+)/.*|\1|')

# if no user‐dir found, skip
[ -z "$USER_DIR" ] && exit 0

PREFIX="($USER_DIR)"

# don’t double‐up if it's already there
grep -q "^[^:]+${PREFIX}:" "$MSG_FILE" && exit 0

# insert prefix before the first colon on the first line
if sed --version >/dev/null 2>&1; then
  # GNU sed
  sed -i -E "1 s/^([^:]+):/\\1${PREFIX}:/1" "$MSG_FILE"
else
  # BSD/macOS sed
  sed -i .bak -E "1 s/^([^:]+):/\\1${PREFIX}:/1" "$MSG_FILE" && rm -f "${MSG_FILE}.bak"
fi

exit 0
