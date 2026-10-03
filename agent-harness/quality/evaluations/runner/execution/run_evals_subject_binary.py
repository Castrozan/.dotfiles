import os
import shutil

INTERACTIVE_WRAPPER_MARKER = b"--append-system-prompt-file"
SUBJECT_BINARY_OVERRIDE = "AGENT_EVAL_CLAUDE_BINARY"
SHELL_SCRIPT_PREFIX = b"#!"
SCRIPT_HEAD_BYTES = 65536


def appends_the_interactive_surface(binary_path: str) -> bool:
    try:
        with open(binary_path, "rb") as binary_file:
            head = binary_file.read(SCRIPT_HEAD_BYTES)
    except OSError:
        return False
    if not head.startswith(SHELL_SCRIPT_PREFIX):
        return False
    return INTERACTIVE_WRAPPER_MARKER in head


def resolve_subject_claude_binary() -> str:
    override = os.environ.get(SUBJECT_BINARY_OVERRIDE, "")
    if override:
        return override
    candidate = _first_unwrapped_claude_binary(os.environ.get("PATH", ""))
    if candidate:
        return candidate
    raise RuntimeError(
        "every claude on PATH is the interactive wrapper, which appends the always-on "
        "reply-shape surface to every launch even under `-p --system-prompt`, so each "
        "sample would score the live machine instead of the instruction paths the suite "
        f"declares; run the packaged agent-eval command, or point {SUBJECT_BINARY_OVERRIDE} "
        "at the unwrapped claude"
    )


def _first_unwrapped_claude_binary(path_value: str) -> str | None:
    for directory in path_value.split(os.pathsep):
        if not directory:
            continue
        candidate = shutil.which("claude", path=directory)
        if candidate and not appends_the_interactive_surface(candidate):
            return candidate
    return None
