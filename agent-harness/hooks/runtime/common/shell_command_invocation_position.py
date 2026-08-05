COMMAND_INVOCATION_POSITION_PREFIX = (
    r"(?:^|[\n;&|(`{!]|\$\(|&&|\|\||"
    r"\b(?:sudo|exec|nohup|time|xargs|command|if|then|else|elif|do|while|until)\s+"
    r"(?:-\S+\s+)*|"
    r"\benv\s+(?:\S+=\S+\s+)+)\s*"
)

COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD = r"(?=\s|$|[;&|)`])"
