COMMAND_INVOCATION_POSITION_PREFIX = (
    r"(?:^|[\n;&|(`{!]|\$\(|&&|\|\||"
    r"\b(?:sudo|exec|nohup|nice|time|xargs|command|if|then|else|elif|do|while|until)\s+"
    r"(?:-\S+\s+)*|"
    r"\btimeout\s+(?:-\S+\s+)*\S+\s+|"
    r"(?<![\w./-])(?:ba|z|da|k)?sh\s+(?:-\S+\s+)*|"
    r"\benv\s+(?:\S+=\S+\s+)+)\s*"
    r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
)

COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD = r"(?=\s|$|[;&|)`])"
