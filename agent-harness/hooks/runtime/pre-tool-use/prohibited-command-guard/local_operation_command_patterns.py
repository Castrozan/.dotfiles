from shell_command_invocation_position import (
    COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD,
    COMMAND_INVOCATION_POSITION_PREFIX,
)

SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL = "CLAUDE_HEADLESS_SANCTIONED=1"
IANA_TIMEZONE_PATTERN = (
    r"[A-Za-z][A-Za-z0-9._+-]+/[A-Za-z][A-Za-z0-9._+-]+"
    r"(?:/[A-Za-z][A-Za-z0-9._+-]+)?"
)
DATE_INPUT_WITH_IANA_TIMEZONE_PATTERN = (
    rf"{COMMAND_INVOCATION_POSITION_PREFIX}"
    rf"(?P<date_with_inline_iana_timezone>date)\s+(?:[^;&|\n]*?\s)?"
    rf"(?:-d|--date)(?:=|\s+)"
    rf'(?:"[^"\n]*{IANA_TIMEZONE_PATTERN}[^"\n]*"|'
    rf"'[^'\n]*{IANA_TIMEZONE_PATTERN}[^'\n]*'|"
    rf"[^\s;&|]*{IANA_TIMEZONE_PATTERN}[^\s;&|]*)"
)
DATE_INPUT_WITH_IANA_TIMEZONE_DENIAL_REASON = (
    "GNU date does not parse a bare IANA timezone inside -d/--date input. "
    "Prefix the command with TZ=Area/Location instead."
)

LOCAL_OPERATION_BASH_COMMAND_PATTERNS = [
    (
        DATE_INPUT_WITH_IANA_TIMEZONE_PATTERN,
        DATE_INPUT_WITH_IANA_TIMEZONE_DENIAL_REASON,
        None,
        "date_with_inline_iana_timezone",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}git\s+add\s+"
        rf"(?:-A|--all|\.){COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD}",
        "git add -A/--all/. is prohibited; stage specific files (parallel work risk).",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}(?:git|gh\s+repo)\s+clone\s+\S*castrozan[/-]?\.?dotfiles",
        "Cloning castrozan/.dotfiles is prohibited; use 'gh api' for remote access.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}direnv\s+(allow|hook|exec|reload|status|edit|deny|block|prune|version)\b",
        "direnv is prohibited; use 'devenv shell' or 'devenv shell -- command'.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}herdr\s+agent\s+start\b(?:(?!\s--tab(?=[\s=]))(?!\s--\s)[^;&|\n])*(?:$|[;&|\n]|\s--\s)",
        "herdr agent start splits an active tab someone is working in, and "
        "--workspace alone is not a pin. Spawn a new agent alone in a fresh tab's "
        "own pane instead, or pin --tab with --no-focus for a deliberate split; "
        "the herdr skill carries both.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}herdr\s+(?:workspace|tab|pane)\s+close\b",
        "Only the human runs a herdr workspace/tab/pane close. The command itself "
        "is fine; ids are reassigned as tabs come and go, so a close can land on "
        "whichever tab inherited the id, and it takes every agent inside with no "
        "undo. Hand that exact command to the human to run, and name what is in "
        "the target; the herdr skill's knowledge covers why the id moves.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}claude(?![\w-])[^;&|`)\n]*?\s(?:-p|--print)(?:[=\s'\"]|$)",
        "claude -p/--print (headless oneshot) is prohibited; drive an interactive "
        "session instead, by launching claude plainly or through a herdr agent as "
        "the herdr skill describes. A sanctioned one-off needs the prefix "
        f"{SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL}.",
        SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL,
    ),
]
