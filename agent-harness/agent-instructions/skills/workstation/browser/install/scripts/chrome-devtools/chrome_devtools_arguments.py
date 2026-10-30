from __future__ import annotations


def following_argument(arguments, index):
    return arguments[index + 1] if index + 1 < len(arguments) else "true"


def headless_requested(arguments):
    enabled = False
    for index, argument in enumerate(arguments):
        if argument.startswith("--headless="):
            enabled = argument.partition("=")[2].lower() == "true"
        elif argument == "--headless":
            value = following_argument(arguments, index)
            enabled = value.lower() != "false"
        elif argument == "--no-headless":
            enabled = False
    return enabled


def validate_session_arguments(arguments):
    if any(argument.startswith("--sessionId") for argument in arguments):
        raise ValueError("Chrome DevTools session ownership is managed automatically")


def inspection_requested(arguments, operation):
    return (
        not arguments or "--help" in arguments or operation in ("--version", "status")
    )
