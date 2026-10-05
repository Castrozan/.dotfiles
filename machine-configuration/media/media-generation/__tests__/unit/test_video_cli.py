import contextlib
import io
import json
import os
import subprocess
import sys
import unittest
import uuid
from dataclasses import asdict
from unittest.mock import patch

import media_video_cli
from video_fixture import FixtureRecipe, SCRIPTS_DIRECTORY, write_json
from media_video.service import VideoService


class JsonCliTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FixtureRecipe()
        self.addCleanup(self.fixture.cleanup)
        self.operation_id = str(uuid.uuid4())
        self.request_file = self.fixture.root / "request.json"
        write_json(
            self.request_file,
            {"operation_id": self.operation_id, **asdict(self.fixture.request)},
        )

    def invoke(self, arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = media_video_cli.main(
                ["--state-directory", str(self.fixture.state), *arguments]
            )
        return code, stdout.getvalue(), stderr.getvalue()

    def test_render_json_and_inspect_use_same_owned_artifacts(self):
        with patch.object(
            media_video_cli, "FframesRenderer", return_value=self.fixture.renderer
        ):
            code, stdout, stderr = self.invoke(
                ["render", "--request-file", str(self.request_file)]
            )
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        receipt = json.loads(stdout)
        calls = list(self.fixture.commands.calls)
        with patch.object(
            media_video_cli,
            "FframesRenderer",
            side_effect=AssertionError("no adapter on inspect"),
        ):
            code, inspected, stderr = self.invoke(["inspect", self.operation_id])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(inspected), receipt)
        self.assertEqual(self.fixture.commands.calls, calls)

    def test_invalid_request_never_constructs_renderer(self):
        document = json.loads(self.request_file.read_bytes())
        document["width"] = 1920
        write_json(self.request_file, document)
        with patch.object(
            media_video_cli,
            "FframesRenderer",
            side_effect=AssertionError("no dispatch"),
        ):
            code, stdout, stderr = self.invoke(
                ["render", "--request-file", str(self.request_file)]
            )
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(json.loads(stderr), {"error": "unsupported_video_contract"})
        self.assertFalse(self.fixture.state.exists())

    def test_unknown_uuid_and_malformed_uuid_return_bounded_json(self):
        for operation_id, category in (
            (self.operation_id, "operation_unavailable"),
            ("../escape", "invalid_operation_id"),
        ):
            code, stdout, stderr = self.invoke(["inspect", operation_id])
            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assertEqual(json.loads(stderr), {"error": category})

    def test_unknown_request_fields_are_refused(self):
        document = json.loads(self.request_file.read_bytes())
        document["shell_command"] = "untrusted"
        write_json(self.request_file, document)
        code, stdout, stderr = self.invoke(
            ["render", "--request-file", str(self.request_file)]
        )
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stderr), {"error": "invalid_request"})
        self.assertEqual(self.fixture.commands.calls, [])

    def test_separate_process_inspect_runs_without_any_adapter(self):
        expected = VideoService(self.fixture.state).render(
            self.operation_id, self.fixture.request, self.fixture.renderer
        )
        process = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPTS_DIRECTORY / "media_video_cli.py"),
                "--state-directory",
                str(self.fixture.state),
                "inspect",
                self.operation_id,
            ],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=self.fixture.root,
            env={**os.environ, "PATH": "/unavailable", "PYTHONPATH": ""},
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout), expected)
        self.assertEqual(len(self.fixture.commands.calls), 4)

    def test_default_state_uses_xdg_without_creating_an_operation(self):
        with patch.dict(os.environ, {"XDG_STATE_HOME": str(self.fixture.root)}):
            parser = media_video_cli.build_parser()
            arguments = parser.parse_args(["inspect", self.operation_id])
            self.assertEqual(
                arguments.state_directory, self.fixture.root / "media-video"
            )
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = media_video_cli.main(["inspect", self.operation_id])
            self.assertEqual(code, 1)
            self.assertEqual(
                json.loads(stderr.getvalue())["error"], "operation_unavailable"
            )
            self.assertFalse(arguments.state_directory.exists())
