import signal
import subprocess
import sys
import time
from pathlib import Path

mode, directory = sys.argv[1:]
directory = Path(directory)
if mode == "storage":
    (directory / "storage-ready").touch()
    if sys.stdin.readline().strip() == "flush":
        (directory / "persisted").write_text("retained")
    sys.exit(0)

storage = subprocess.Popen(
    [sys.executable, __file__, "storage", str(directory)],
    stdin=subprocess.PIPE,
    text=True,
)


def shutdown(number, frame):
    time.sleep(0.1)
    storage.communicate("flush\n", timeout=2)
    sys.exit(storage.returncode)


signal.signal(signal.SIGTERM, shutdown)
while not (directory / "storage-ready").exists():
    time.sleep(0.01)
(directory / "browser-ready").touch()
while True:
    time.sleep(1)
