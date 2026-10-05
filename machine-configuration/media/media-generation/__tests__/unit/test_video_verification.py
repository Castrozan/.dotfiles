import copy
import unittest
import uuid
from dataclasses import replace

from video_fixture import FixtureRecipe, probe_document
from media_video.contract import VideoError
from media_video.service import VideoService
from media_video.verification import validate_probe


class VideoVerificationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FixtureRecipe()
        self.addCleanup(self.fixture.cleanup)

    def test_requested_and_measured_durations_are_distinct(self):
        measured = validate_probe(probe_document(), self.fixture.request)
        self.assertEqual(measured["video_duration_seconds"], 60)
        self.assertEqual(measured["container_duration_seconds"], 60.053333)
        self.assertEqual(measured["frame_count"], 1800)

    def test_container_padding_limit_is_inclusive_and_bounded(self):
        probe = probe_document()
        for duration in ("60.000000", "60.100000"):
            probe["format"]["duration"] = duration
            validate_probe(probe, self.fixture.request)
        for duration in ("59.999999", "60.100001", "NaN"):
            probe["format"]["duration"] = duration
            with self.assertRaisesRegex(VideoError, "video_contract_mismatch"):
                validate_probe(probe, self.fixture.request)

    def test_dimension_fps_frame_count_codec_and_duration_errors_are_refused(self):
        for key, value in (
            ("width", 720),
            ("height", 1280),
            ("avg_frame_rate", "24/1"),
            ("r_frame_rate", "24/1"),
            ("nb_read_frames", "1799"),
            ("duration", "59.999"),
            ("codec_name", ""),
        ):
            probe = probe_document()
            probe["streams"][0][key] = value
            with self.assertRaisesRegex(VideoError, "video_contract_mismatch"):
                validate_probe(probe, self.fixture.request)

    def test_missing_audio_irregular_frames_and_wrong_container_are_refused(self):
        original = probe_document()
        changed = copy.deepcopy(original)
        changed["streams"] = changed["streams"][:1]
        irregular = copy.deepcopy(original)
        irregular["frames"][80]["best_effort_timestamp_time"] = "100"
        bad_container = copy.deepcopy(original)
        bad_container["format"]["format_name"] = "matroska"
        for probe in (changed, irregular, bad_container):
            with self.assertRaisesRegex(VideoError, "video_contract_mismatch"):
                validate_probe(probe, self.fixture.request)

    def test_failed_media_contract_retains_video_without_thumbnail_or_success(self):
        self.fixture.commands.probe["streams"][0]["width"] = 720
        service = VideoService(self.fixture.state)
        operation_id = str(uuid.uuid4())
        with self.assertRaisesRegex(VideoError, "video_contract_mismatch"):
            service.render(operation_id, self.fixture.request, self.fixture.renderer)
        receipt = service.inspect(operation_id)
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(
            [entry[0] for entry in self.fixture.commands.calls], ["render", "probe"]
        )

    def test_arguments_are_fixed_and_execution_uses_retained_recipe(self):
        request = replace(self.fixture.request, episode_id="$(touch escape);episode")
        service = VideoService(self.fixture.state)
        operation_id = str(uuid.uuid4())
        service.render(operation_id, request, self.fixture.renderer)
        step, arguments, working_directory = self.fixture.commands.calls[0]
        directory = self.fixture.state / operation_id
        self.assertEqual(step, "render")
        self.assertEqual(
            arguments,
            [directory / "inputs/renderer", "render", "-o", directory / "render.mp4"],
        )
        self.assertEqual(working_directory, directory / "inputs/recipe")
        self.assertNotIn(request.episode_id, [str(item) for item in arguments])
