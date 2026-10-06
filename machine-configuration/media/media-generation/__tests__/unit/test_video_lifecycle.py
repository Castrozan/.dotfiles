import os
import time
import unittest
import uuid
from dataclasses import replace
from unittest.mock import patch

from video_fixture import FixtureRecipe
from media_video.contract import VideoError
from media_video.service import VideoService


class VideoLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FixtureRecipe()
        self.addCleanup(self.fixture.cleanup)
        self.service = VideoService(self.fixture.state)
        self.operation_id = str(uuid.uuid4())

    def render(self, request=None):
        return self.service.render(
            self.operation_id, request or self.fixture.request, self.fixture.renderer
        )

    def test_input_change_between_preflight_and_copy_never_dispatches(self):
        preflight = self.fixture.renderer.preflight

        def mutate_after_preflight(request, deadline):
            recipe = preflight(request, deadline)
            self.fixture.asset.write_bytes(b"changed during claim")
            return recipe

        with patch.object(
            self.fixture.renderer, "preflight", side_effect=mutate_after_preflight
        ):
            with self.assertRaisesRegex(VideoError, "registered_input_changed"):
                self.render()
        receipt = self.service.inspect(self.operation_id)
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(self.fixture.commands.calls, [])
        self.assertTrue(
            (
                self.fixture.state / self.operation_id / "inputs/registration.json"
            ).exists()
        )

    def test_renderer_cannot_promote_mutated_retained_inputs(self):
        run = self.fixture.commands.run

        def mutate_snapshot(step, arguments, cwd, logs, deadline):
            result = run(step, arguments, cwd, logs, deadline)
            if step == "render":
                (cwd / "main.rs").write_bytes(b"changed retained source")
            return result

        with patch.object(self.fixture.commands, "run", side_effect=mutate_snapshot):
            with self.assertRaisesRegex(VideoError, "input_checksum_mismatch"):
                self.render()
        self.assertEqual(self.service.inspect(self.operation_id)["status"], "failed")
        with self.assertRaisesRegex(VideoError, "operation_incomplete"):
            self.render()
        self.assertEqual(len(self.fixture.commands.calls), 4)

    def test_whole_job_timeout_retains_failed_receipt_without_retry(self):
        run = self.fixture.commands.run
        request = replace(self.fixture.request, deadline_seconds=0.5)

        def exceed_deadline(step, arguments, cwd, logs, deadline):
            result = run(step, arguments, cwd, logs, deadline)
            if step == "render":
                time.sleep(0.6)
            deadline.remaining()
            return result

        with patch.object(self.fixture.commands, "run", side_effect=exceed_deadline):
            with self.assertRaisesRegex(VideoError, "deadline_exceeded"):
                self.render(request)
        receipt = self.service.inspect(self.operation_id)
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["error"], "deadline_exceeded")
        self.assertGreaterEqual(receipt["elapsed_seconds"], 0.5)
        self.assertTrue(receipt["retained_inputs"])
        with self.assertRaisesRegex(VideoError, "operation_incomplete"):
            self.render(request)
        self.assertEqual(len(self.fixture.commands.calls), 1)

    def test_output_durability_failure_cannot_become_success(self):
        fsync = os.fsync

        def fail_video_sync(descriptor):
            path = self.fixture.state / self.operation_id / "render.mp4"
            if path.exists() and os.fstat(descriptor).st_ino == path.stat().st_ino:
                raise OSError("fixture output sync failure")
            return fsync(descriptor)

        with patch("media_video.files.os.fsync", side_effect=fail_video_sync):
            with self.assertRaisesRegex(VideoError, "render_failed"):
                self.render()
        self.assertEqual(self.service.inspect(self.operation_id)["status"], "failed")
        with self.assertRaisesRegex(VideoError, "operation_incomplete"):
            self.render()
        self.assertEqual(len(self.fixture.commands.calls), 4)
