import os
import pathlib
from typing import NamedTuple


ENVIRONMENT_VARIABLE = "HERDR_RUNNING_SERVER_RECORD"


class RunningServer(NamedTuple):
    socket_path: pathlib.Path
    process_identifier: int
    executable: pathlib.Path


def record_running_server(record_path, running_server):
    temporary_path = record_path.with_name(f"{record_path.name}.{os.getpid()}")
    try:
        record_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path.write_text(
            f"{running_server.socket_path}\n{running_server.process_identifier}\n"
        )
        os.replace(temporary_path, record_path)
    except OSError:
        return
