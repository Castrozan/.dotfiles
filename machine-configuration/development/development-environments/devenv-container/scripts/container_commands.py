import os
import signal
import subprocess

TERMINATION_GRACE_SECONDS = 5


def interrupt_command(_command_signal, _stack_frame):
    raise KeyboardInterrupt


def terminate_command(process, interactive, termination_grace_seconds):
    def send(command_signal):
        try:
            if interactive:
                process.send_signal(command_signal)
            else:
                os.killpg(process.pid, command_signal)
        except ProcessLookupError:
            pass

    send(signal.SIGTERM)
    try:
        process.communicate(timeout=termination_grace_seconds)
    except subprocess.TimeoutExpired:
        send(signal.SIGKILL)
        process.communicate(timeout=TERMINATION_GRACE_SECONDS)


def run_command(
    arguments,
    environment,
    *,
    capture=False,
    timeout=60,
    check=True,
    interactive=False,
    termination_grace_seconds=TERMINATION_GRACE_SECONDS,
):
    process = subprocess.Popen(
        arguments,
        env=environment,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        start_new_session=not interactive,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        terminate_command(process, interactive, termination_grace_seconds)
        raise
    result = subprocess.CompletedProcess(arguments, process.returncode, stdout, stderr)
    if check:
        result.check_returncode()
    return result
