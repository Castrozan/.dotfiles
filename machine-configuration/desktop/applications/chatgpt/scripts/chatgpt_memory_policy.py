OPEN_WINDOW_MEMORY_HIGH_BYTES = 4 * 1024**3
BACKGROUND_MEMORY_HIGH_BYTES = 1536 * 1024**2
STARTUP_HEADROOM_SECONDS = 30


def memory_high_for_window_state(
    window_open: bool | None, elapsed_seconds: float
) -> int:
    if window_open is not False or elapsed_seconds < STARTUP_HEADROOM_SECONDS:
        return OPEN_WINDOW_MEMORY_HIGH_BYTES
    return BACKGROUND_MEMORY_HIGH_BYTES
