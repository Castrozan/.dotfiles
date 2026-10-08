import subprocess
import sys
import time
import unittest

from video_fixture import FixtureRecipe
from media_video.contract import VideoError
from media_video.deadline import ExecutionDeadline
from media_video.process import CommandRunner


class ProcessBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FixtureRecipe()
        self.addCleanup(self.fixture.cleanup)
        self.runner = CommandRunner()

    def test_process_failure_retains_both_logs(self):
        logs_directory = self.fixture.root / "logs"
        deadline = ExecutionDeadline(2)
        with self.assertRaisesRegex(VideoError, "render_failed"):
            self.runner.run(
                "render",
                [
                    sys.executable,
                    "-c",
                    "import sys\nprint('partial output')\nprint('private error',file=sys.stderr)\nsys.exit(7)",
                ],
                self.fixture.recipe,
                logs_directory,
                deadline,
            )
        self.assertIn(
            "partial output", (self.fixture.root / "logs/render.stdout.log").read_text()
        )
        self.assertIn(
            "private error", (self.fixture.root / "logs/render.stderr.log").read_text()
        )

    def test_timeout_terminates_ignoring_descendant_process(self):
        child = "import signal,time\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\ntime.sleep(30)"
        program = (
            "import subprocess,sys,time\nfrom pathlib import Path\n"
            f"child=subprocess.Popen([sys.executable,'-c',{child!r}])\n"
            "Path('child.pid').write_text(str(child.pid))\n"
            "print('parent ready',flush=True)\ntime.sleep(30)"
        )
        started = time.monotonic()
        logs_directory = self.fixture.root / "logs"
        deadline = ExecutionDeadline(0.6)
        with self.assertRaisesRegex(VideoError, "deadline_exceeded"):
            self.runner.run(
                "render",
                [sys.executable, "-c", program],
                self.fixture.recipe,
                logs_directory,
                deadline,
            )
        child_pid = (self.fixture.recipe / "child.pid").read_text()
        while time.monotonic() - started < 2:
            process = subprocess.run(
                [
                    "/bin/ps" if sys.platform == "darwin" else "ps",
                    "-o",
                    "stat=",
                    "-p",
                    child_pid,
                ],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if process.returncode != 0 or process.stdout.strip().startswith("Z"):
                break
            time.sleep(0.02)
        else:
            self.fail("timed out waiting for the descendant process to terminate")
        self.assertTrue((self.fixture.root / "logs/render.stdout.log").is_file())

    def test_expired_deadline_never_starts_process(self):
        deadline = ExecutionDeadline(0.001)
        time.sleep(0.01)
        with self.assertRaisesRegex(VideoError, "deadline_exceeded"):
            self.runner.run(
                "render",
                [sys.executable, "-c", "raise RuntimeError('must not run')"],
                self.fixture.recipe,
                self.fixture.root / "logs",
                deadline,
            )
