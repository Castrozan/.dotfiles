import importlib
import os
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

mode, scenario, directory, runtime = sys.argv[1:]
directory = Path(directory)
sys.path.insert(0, runtime)
if mode == "payload":
    (directory / "payload-ready").touch()
    while True:
        time.sleep(1)

if mode == "controller":
    from opencli_supervisor import supervise_process

    raise SystemExit(
        supervise_process(
            [sys.executable, __file__, "worker", scenario, str(directory), runtime]
        )
    )

opencli_job = importlib.import_module("opencli_job")

(directory / "worker.pid").write_text(str(os.getpid()))
for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
    signal.signal(number, opencli_job.interrupted)


@contextmanager
def isolated_job(*arguments):
    yield dict(os.environ)


original_process = subprocess.Popen


def disappear_after_spawn(*arguments, **options):
    process = original_process(*arguments, **options)
    (directory / "child.pid").write_text(str(process.pid))
    if scenario == "worker":
        os._exit(0)
    deadline = time.monotonic() + 10
    while not (directory / "payload-ready").exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert (directory / "payload-ready").exists()
    os.kill(os.getppid(), signal.SIGKILL)
    time.sleep(0.3)
    return process


opencli_job.browser_job = isolated_job
subprocess.Popen = disappear_after_spawn
options = SimpleNamespace(
    worker=True,
    profile="startup",
    headed=False,
    timeout=30,
    command=[
        sys.executable,
        __file__,
        "payload",
        scenario,
        str(directory),
        runtime,
    ],
)
raise SystemExit(opencli_job.execute(options))
