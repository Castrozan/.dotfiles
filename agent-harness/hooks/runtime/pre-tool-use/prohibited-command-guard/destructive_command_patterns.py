from shell_command_invocation_position import (
    COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD,
    COMMAND_INVOCATION_POSITION_PREFIX,
)

DESTRUCTIVE_COMMAND_DENIAL_REASON = (
    "This agent may not run destructive system commands. Ask the human to run it."
)

DESTRUCTIVE_COMMAND_PATTERN = (
    rf"{COMMAND_INVOCATION_POSITION_PREFIX}"
    rf"(?P<destructive_command>"
    rf"sudo|rm|rmdir|dd|mkfs(?:\.[^\s;&|]+)?|fdisk|shutdown|reboot|halt|poweroff"
    rf"){COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD}"
)

DESTRUCTIVE_BASH_COMMAND_PATTERNS = [
    (
        DESTRUCTIVE_COMMAND_PATTERN,
        DESTRUCTIVE_COMMAND_DENIAL_REASON,
        None,
        "destructive_command",
    ),
]

DESTRUCTIVE_PATTERNS_BY_TOOL = {
    "Bash": DESTRUCTIVE_BASH_COMMAND_PATTERNS,
}
