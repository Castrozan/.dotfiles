from __future__ import annotations


def attached_idle_allowance(arguments):
    option = "--keep-attached-for"
    if option not in arguments:
        return None
    index = arguments.index(option)
    try:
        return float(arguments[index + 1])
    except (IndexError, ValueError):
        raise ValueError(f"{option} needs a number of seconds") from None


def keeps_attached_worker(session, arguments):
    allowance = attached_idle_allowance(arguments)
    return (
        allowance is not None
        and session.mode() == "attached"
        and session.idle_seconds() < allowance
    )
