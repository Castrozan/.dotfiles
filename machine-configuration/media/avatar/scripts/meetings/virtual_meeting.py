import subprocess


def unit_states(units, timeout_seconds):
    observed = subprocess.run(
        ["systemctl", "--user", "is-active", *units],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if observed.returncode not in (0, 3) or not observed.stdout.strip():
        raise RuntimeError("Avatar resource state could not be established")
    return observed.stdout.splitlines()


def require_fresh_runtime(units, audio_ready, timeout_seconds):
    states = unit_states(units, timeout_seconds)
    if (
        any(state in {"active", "activating", "reloading"} for state in states)
        or audio_ready()
    ):
        raise RuntimeError(
            "Existing avatar resources must be left untouched; virtual-only start refused"
        )
