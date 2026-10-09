import importlib.util
import os
import pty
import select
import shlex
import signal
import subprocess
import sys
import time

from exclusive_run_lock_support import EXCLUSIVE_RUN_LOCK_HELPER_PATH


def test_scope_keeps_native_authentication_input_in_the_foreground(
    unique_lock_name_with_cleanup, tmp_path
):
    native = tmp_path / "native_authentication.py"
    native.write_text(
        "import os\n"
        "assert os.tcgetpgrp(0) == os.getpgrp()\n"
        "print('AUTH_READY', flush=True)\n"
        "assert input() == 'authorized input'\n"
        "print('AUTH_COMPLETE', flush=True)\n"
    )
    scope = EXCLUSIVE_RUN_LOCK_HELPER_PATH.with_name("exclusive_run_scope.py")
    command = shlex.join([sys.executable, str(scope)])
    native_command = shlex.join([sys.executable, str(native)])
    program = f'''source "{EXCLUSIVE_RUN_LOCK_HELPER_PATH}"
acquire_exclusive_run_lock_or_emit_retry_instructions "{unique_lock_name_with_cleanup}" 60
exec {command} "$DOTFILES_EXCLUSIVE_RUN_LOCK_FILE_DESCRIPTOR" {native_command}
'''
    child, terminal = pty.fork()
    if child == 0:
        os.execvp("bash", ["bash", "-c", program])
    output = b""
    supplied_input = False
    child_reaped = False
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            readable, _, _ = select.select([terminal], [], [], 0.05)
            if not readable:
                continue
            try:
                data = os.read(terminal, 4096)
            except OSError:
                break
            if not data:
                break
            output += data
            if b"AUTH_READY" in output and not supplied_input:
                os.write(terminal, b"authorized input\n")
                supplied_input = True
            if b"AUTH_COMPLETE" in output:
                break
        assert b"AUTH_COMPLETE" in output, output.decode()
        _, exit_status = os.waitpid(child, 0)
        child_reaped = True
        assert os.waitstatus_to_exitcode(exit_status) == 0, output.decode()
    finally:
        if not child_reaped:
            try:
                os.kill(child, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(child, 0)
        os.close(terminal)


def test_native_exit_before_terminal_handoff_preserves_status(tmp_path, monkeypatch):
    scope_path = EXCLUSIVE_RUN_LOCK_HELPER_PATH.with_name("exclusive_run_scope.py")
    module_specification = importlib.util.spec_from_file_location("scope", scope_path)
    scope = importlib.util.module_from_spec(module_specification)
    module_specification.loader.exec_module(scope)
    original_process_constructor = subprocess.Popen

    def finish_native_before_handoff(*arguments, **keyword_arguments):
        native = original_process_constructor(*arguments, **keyword_arguments)
        native.wait(timeout=5)
        return native

    monkeypatch.setattr(scope.subprocess, "Popen", finish_native_before_handoff)
    child, terminal = pty.fork()
    if child == 0:
        descriptor = os.open(tmp_path / "lock", os.O_RDONLY | os.O_CREAT, 0o600)
        sys.argv = ["scope", str(descriptor), "bash", "-c", "exit 42"]
        os._exit(scope.main())
    output = b""
    try:
        while True:
            try:
                data = os.read(terminal, 4096)
            except OSError:
                break
            if not data:
                break
            output += data
        _, exit_status = os.waitpid(child, 0)
        assert os.waitstatus_to_exitcode(exit_status) == 42, output.decode()
    finally:
        os.close(terminal)
