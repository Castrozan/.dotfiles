import os
import subprocess


def spawn_detached(arguments):
    child = os.fork()
    if child:
        _, status = os.waitpid(child, 0)
        if os.waitstatus_to_exitcode(status) != 0:
            raise OSError("detached process did not start")
        return
    exit_code = 1
    try:
        subprocess.Popen(
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
        exit_code = 0
    finally:
        os._exit(exit_code)
