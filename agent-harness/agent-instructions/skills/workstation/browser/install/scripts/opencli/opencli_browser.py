import fcntl
import os
import subprocess
import sys
from contextlib import ExitStack, contextmanager


@contextmanager
def browser_process(arguments, environment, output):
    with ExitStack() as resources:
        browser_input, control_input = os.pipe()
        browser_input = resources.enter_context(
            os.fdopen(browser_input, "rb", buffering=0)
        )
        control_input = resources.enter_context(
            os.fdopen(control_input, "wb", buffering=0)
        )
        control_output, browser_output = os.pipe()
        control_output = resources.enter_context(
            os.fdopen(control_output, "rb", buffering=0)
        )
        browser_output = resources.enter_context(
            os.fdopen(browser_output, "wb", buffering=0)
        )
        process = subprocess.Popen(
            [
                sys.executable,
                __file__,
                str(browser_input.fileno()),
                str(browser_output.fileno()),
                *arguments,
            ],
            pass_fds=(browser_input.fileno(), browser_output.fileno()),
            env=environment,
            stdout=output,
            stderr=output,
            start_new_session=True,
        )
        browser_input.close()
        browser_output.close()
        try:
            yield process
        finally:
            close_browser(process, control_input)


def close_browser(process, control):
    if process.poll() is not None:
        return
    try:
        control.write(b'{"id":1,"method":"Browser.close"}\x00')
        process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        pass


def execute_browser():
    browser_input, browser_output = map(int, sys.argv[1:3])
    input_copy = fcntl.fcntl(browser_input, fcntl.F_DUPFD, 5)
    output_copy = fcntl.fcntl(browser_output, fcntl.F_DUPFD, 5)
    os.dup2(input_copy, 3, inheritable=True)
    os.dup2(output_copy, 4, inheritable=True)
    for descriptor in {browser_input, browser_output, input_copy, output_copy} - {3, 4}:
        os.close(descriptor)
    os.execv(sys.argv[3], sys.argv[3:])


if __name__ == "__main__":
    execute_browser()
