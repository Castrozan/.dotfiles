from reply_format_configuration import REPLY_FORMAT_CONFIGURATION


def bounce_guidance(
    violations: list[str], configuration=REPLY_FORMAT_CONFIGURATION
) -> str:
    return (
        configuration.feedback["prefix"]
        + " ("
        + "; ".join(violations)
        + "). "
        + configuration.feedback["repair"]
    )
