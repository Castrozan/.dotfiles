"""Launcher contract tests without creating namespaces or running system tools."""

import os
import pathlib
import runpy
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts/run.py"


class RunnerTests(unittest.TestCase):
    def test_runtime_and_readonly_host(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"DOT_ROOT": directory}):
                with patch("sys.argv", [str(SCRIPT), "nix", "--version"]):
                    with patch("os.execvp") as execute:
                        runpy.run_path(str(SCRIPT), run_name="__main__")
            program, args = execute.call_args.args
            self.assertEqual(program, "bwrap")
            self.assertEqual(args[-2:], ["nix", "--version"])
            self.assertIn("--unshare-user", args)
            self.assertIn("--unshare-pid", args)
            self.assertIn("--remount-ro", args)
            binds = [
                args[i + 1 : i + 3] for i, value in enumerate(args) if value == "--bind"
            ]
            self.assertEqual(
                binds,
                [
                    [directory, directory],
                    [directory + "/store", "/nix"],
                    [directory + "/tmp", "/tmp"],
                ],
            )
            self.assertTrue(pathlib.Path(directory, "home").is_dir())

    def test_refuse_writable_source_ancestor(self):
        with patch.dict(os.environ, {"DOT_ROOT": str(SCRIPT.parent)}):
            with self.assertRaisesRegex(SystemExit, "must not contain"):
                runpy.run_path(str(SCRIPT), run_name="__main__")


if __name__ == "__main__":
    unittest.main()
