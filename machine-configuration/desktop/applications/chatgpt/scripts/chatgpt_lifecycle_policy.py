STARTUP_HEADROOM_SECONDS = 30
WINDOWLESS_GRACE_SECONDS = 5


def app_should_quit(
    window_open: bool | None, elapsed_seconds: float, windowless_seconds: float
) -> bool:
    return (
        window_open is False
        and elapsed_seconds >= STARTUP_HEADROOM_SECONDS
        and windowless_seconds >= WINDOWLESS_GRACE_SECONDS
    )
