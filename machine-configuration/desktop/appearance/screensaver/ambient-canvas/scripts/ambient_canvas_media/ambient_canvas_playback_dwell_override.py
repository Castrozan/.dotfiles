SHORTEST_ALLOWED_DWELL_SECONDS = 2.0


def read_requested_dwell_seconds(override_file_path):
    if not override_file_path:
        return None
    try:
        with open(override_file_path, encoding="utf-8") as override_file:
            return float(override_file.read().strip())
    except (OSError, ValueError):
        return None


def effective_dwell_seconds(recorded_dwell_seconds, override_file_path):
    requested_dwell_seconds = read_requested_dwell_seconds(override_file_path)
    if requested_dwell_seconds is None:
        return recorded_dwell_seconds
    return min(
        recorded_dwell_seconds,
        max(SHORTEST_ALLOWED_DWELL_SECONDS, requested_dwell_seconds),
    )
