import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from video_fixture import FixtureRecipe
from media_video.contract import VideoError
from media_video.service import VideoService


class VideoJobTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FixtureRecipe()
        self.addCleanup(self.fixture.cleanup)
        self.service = VideoService(self.fixture.state)
        self.operation_id = str(uuid.uuid4())

    def render(self):
        return self.service.render(
            self.operation_id, self.fixture.request, self.fixture.renderer
        )

    def test_single_dispatch_replay_and_inspect_keep_exact_receipt(self):
        receipt = self.render()
        calls = list(self.fixture.commands.calls)
        self.assertEqual(self.render(), receipt)
        self.assertEqual(self.service.inspect(self.operation_id), receipt)
        self.assertEqual(self.fixture.commands.calls, calls)
        self.assertEqual(
            [call[0] for call in calls], ["render", "probe", "decode", "thumbnail"]
        )
        self.assertEqual(receipt["cost"]["generative_provider_calls"], 0)
        self.assertIsNone(receipt["cost"]["compute_cost_usd"])

    def test_attribution_conflict_does_not_dispatch(self):
        self.render()
        conflicting_request = replace(self.fixture.request, episode_id="other")
        with self.assertRaisesRegex(VideoError, "operation_conflict"):
            self.service.render(
                self.operation_id,
                conflicting_request,
                self.fixture.renderer,
            )
        self.assertEqual(len(self.fixture.commands.calls), 4)

    def test_changed_assets_refused_before_claim(self):
        self.fixture.asset.write_bytes(b"changed")
        with self.assertRaisesRegex(VideoError, "registered_input_changed"):
            self.render()
        self.assertFalse(self.fixture.state.exists())
        self.assertEqual(self.fixture.commands.calls, [])

    def test_new_registration_of_changed_input_conflicts_with_existing_uuid(self):
        self.render()
        self.fixture.asset.write_bytes(b"newly registered")
        self.fixture.refresh()
        with self.assertRaisesRegex(VideoError, "operation_conflict"):
            self.render()
        self.assertEqual(len(self.fixture.commands.calls), 4)

    def test_video_and_thumbnail_checksum_failures_prevent_replay(self):
        receipt = self.render()
        for asset in receipt["assets"].values():
            from pathlib import Path

            path = Path(asset["path"])
            original = path.read_bytes()
            path.write_bytes(b"corrupt")
            with self.assertRaisesRegex(VideoError, "asset_checksum_mismatch"):
                self.render()
            path.write_bytes(original)
        self.assertEqual(len(self.fixture.commands.calls), 4)

    def test_failed_render_keeps_inputs_logs_and_partial_output(self):
        self.fixture.commands.failure = "render"
        with self.assertRaisesRegex(VideoError, "render_failed"):
            self.render()
        receipt = self.service.inspect(self.operation_id)
        directory = self.fixture.state / self.operation_id
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(
            (directory / "inputs/recipe/narration.wav").read_bytes(),
            self.fixture.asset.read_bytes(),
        )
        self.assertTrue((directory / "render.mp4").is_file())
        self.assertTrue((directory / "logs/render.stdout.log").is_file())
        with self.assertRaisesRegex(VideoError, "operation_incomplete"):
            self.render()
        self.assertEqual(len(self.fixture.commands.calls), 1)

    def test_decode_failure_never_becomes_success(self):
        self.fixture.commands.failure = "decode"
        with self.assertRaisesRegex(VideoError, "decode_failed"):
            self.render()
        self.assertEqual(self.service.inspect(self.operation_id)["status"], "failed")
        self.assertEqual(len(self.fixture.commands.calls), 3)

    def test_missing_receipt_and_interrupted_dispatch_never_redispatch(self):
        self.fixture.state.mkdir(mode=0o700)
        directory = self.fixture.state / self.operation_id
        directory.mkdir(mode=0o700)
        with self.assertRaisesRegex(VideoError, "operation_incomplete"):
            self.render()
        self.assertEqual(self.fixture.commands.calls, [])
        directory.rmdir()
        self.fixture.commands.failure = "render"
        with self.assertRaises(VideoError):
            self.render()
        from media_video.files import atomic_json

        receipt = self.service.inspect(self.operation_id)
        receipt["status"] = "dispatching"
        atomic_json(directory / "receipt.json", receipt)
        with self.assertRaisesRegex(VideoError, "operation_incomplete"):
            self.render()
        self.assertEqual(len(self.fixture.commands.calls), 1)

    def test_simultaneous_callers_claim_uuid_once(self):
        self.fixture.commands.release = threading.Event()
        with ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(self.render)
            self.assertTrue(self.fixture.commands.entered.wait(timeout=1))
            try:
                with self.assertRaisesRegex(VideoError, "operation_incomplete"):
                    self.render()
            finally:
                self.fixture.commands.release.set()
            self.assertEqual(pending.result()["status"], "succeeded")
        self.assertEqual(len(self.fixture.commands.calls), 4)

    def test_input_snapshot_mutation_is_detected(self):
        self.render()
        (self.fixture.state / self.operation_id / "inputs/recipe/main.rs").write_bytes(
            b"tampered"
        )
        with self.assertRaisesRegex(VideoError, "input_checksum_mismatch"):
            self.service.inspect(self.operation_id)
