import os
import subprocess
import sys
import time

import pytest

from session_server_diagnostics import (
    DIAGNOSTIC_FILE_BYTES,
    MAXIMUM_SESSION_DIAGNOSTIC_BYTES,
    MAXIMUM_STARTUP_DIAGNOSTIC_BYTES,
    SessionServerDiagnostics,
)


def emit_backend_output(diagnostics, program):
    process = subprocess.Popen(
        [sys.executable, "-c", program],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=diagnostics.stderr_descriptor,
    )
    diagnostics.close_stderr_descriptor()
    try:
        assert process.wait(timeout=5.0) == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_backend_pipe_drains_and_rotates_with_bounded_session_storage(tmp_path, capfd):
    recent_output = b"b" * (DIAGNOSTIC_FILE_BYTES // 2) + b"\nlatest failure\n"
    with SessionServerDiagnostics(tmp_path) as diagnostics:
        emit_backend_output(
            diagnostics,
            "import os; "
            f"os.write(2, b'a' * {MAXIMUM_SESSION_DIAGNOSTIC_BYTES}); "
            f"os.write(2, b'b' * {DIAGNOSTIC_FILE_BYTES // 2}); "
            "os.write(2, b'\\nlatest failure\\n')",
        )
    assert diagnostics.previous_path.read_bytes() == b"a" * DIAGNOSTIC_FILE_BYTES
    assert diagnostics.current_path.read_bytes() == recent_output
    retained_bytes = sum(path.stat().st_size for path in tmp_path.iterdir())
    assert retained_bytes <= MAXIMUM_SESSION_DIAGNOSTIC_BYTES
    details = diagnostics.startup_failure_details()
    assert details.endswith("latest failure")
    assert len(details.encode("utf-8")) <= MAXIMUM_STARTUP_DIAGNOSTIC_BYTES
    assert capfd.readouterr().err == ""


def test_startup_failure_details_remove_terminal_controls_and_invalid_bytes(tmp_path):
    with SessionServerDiagnostics(tmp_path) as diagnostics:
        emit_backend_output(
            diagnostics,
            "import os; os.write(2, b'\\x1b[31mfailed\\x00\\r\\xff\\n\\tmore')",
        )
    assert diagnostics.current_path.read_bytes() == b"\x1b[31mfailed\x00\r\xff\n\tmore"
    assert diagnostics.startup_failure_details() == "[31mfailed\n\tmore"


def test_diagnostic_shutdown_is_bounded_when_a_descendant_keeps_stderr_open(tmp_path):
    diagnostics = SessionServerDiagnostics(tmp_path)
    with diagnostics:
        inherited_writer = os.dup(diagnostics.stderr_descriptor)
        started_at = time.monotonic()
        diagnostics.close()
        elapsed = time.monotonic() - started_at
        try:
            with pytest.raises(BrokenPipeError):
                os.write(inherited_writer, b"after shutdown")
        finally:
            os.close(inherited_writer)
    assert elapsed < 1.5


def test_diagnostic_storage_failure_keeps_draining_backend_pipe(
    tmp_path, monkeypatch, capfd
):
    def reject_storage(output):
        raise OSError("diagnostic volume is full")

    with SessionServerDiagnostics(tmp_path) as diagnostics:
        monkeypatch.setattr(diagnostics, "_append", reject_storage)
        emit_backend_output(
            diagnostics,
            "import os; "
            f"os.write(2, b'backend output' * {MAXIMUM_SESSION_DIAGNOSTIC_BYTES // 14})",
        )
    assert diagnostics.current_path.stat().st_size == 0
    assert diagnostics.startup_failure_details() == ""
    assert capfd.readouterr().err == ""
