import hashlib
import json
from dataclasses import replace

import pytest

from media_movie.contract import MovieAsset, MovieError
from media_movie.service import MovieService
from media_speech.contract import SpeechError
from test_movie_contract import movie_scene
from media_movie.contract import MovieRequest


class RecordingAssets:
    def __init__(self, directory, fail=False):
        self.directory = directory
        self.calls = []
        self.fail = fail
        self.invalid_scene = None

    def preflight(self, scene):
        self.calls.append("preflight")
        if scene == self.invalid_scene:
            raise SpeechError("unsupported_model")

    def generate_image(self, operation_id, selection):
        self.calls.append("image")
        path = self.directory / f"{operation_id}.png"
        path.write_bytes(b"image fixture")
        return MovieAsset(path, hashlib.sha256(path.read_bytes()).hexdigest())

    def generate_narration(self, operation_id, selection):
        self.calls.append("narration")
        if self.fail:
            raise SpeechError("provider_failed")
        path = self.directory / f"{operation_id}.wav"
        path.write_bytes(b"speech fixture")
        return MovieAsset(path, hashlib.sha256(path.read_bytes()).hexdigest(), 1)


class RecordingAssembler:
    name = "test-assembly"

    def __init__(self):
        self.calls = 0

    def preflight(self, movie_request):
        pass

    def assemble(self, movie_request, scenes, directory):
        self.calls += 1
        (directory / "render.mp4").write_bytes(b"assembled fixture")
        (directory / "thumbnail.png").write_bytes(b"thumbnail fixture")
        return {
            "media": {"frame_count": sum(scene.frames for scene in scenes)},
            "verification": {},
        }


def request_with(*scenes):
    return MovieRequest("jobs", "example", 64, 64, 30, scenes or (movie_scene(),))


def test_replay_and_changed_request_never_dispatch(tmp_path, operation_id):
    assets = RecordingAssets(tmp_path)
    assembler = RecordingAssembler()
    service = MovieService(tmp_path / "state", assets, assembler)
    movie_request = request_with()
    receipt = service.generate(operation_id, movie_request)
    calls = list(assets.calls)
    assert service.generate(operation_id, movie_request) == receipt
    with pytest.raises(MovieError, match="operation_conflict"):
        service.generate(operation_id, replace(movie_request, episode_id="other"))
    assert assembler.calls == 1
    assert assets.calls == calls
    assert len(receipt["child_operations"]) == 1
    assert len(receipt["retained_inputs"]) == 2


def test_all_scene_preflights_run_before_any_paid_generation(tmp_path, operation_id):
    assets = RecordingAssets(tmp_path)
    bad_scene = replace(movie_scene(), motion="static")
    assets.invalid_scene = bad_scene
    service = MovieService(tmp_path / "state", assets, RecordingAssembler())
    with pytest.raises(SpeechError, match="unsupported_model"):
        service.generate(operation_id, request_with(movie_scene(), bad_scene))
    assert assets.calls == ["preflight", "preflight"]
    assert not service.state_directory.exists()


def test_partial_failure_retains_inputs_and_child_ids_without_redispatch(
    tmp_path, operation_id
):
    assets = RecordingAssets(tmp_path, fail=True)
    service = MovieService(tmp_path / "state", assets, RecordingAssembler())
    with pytest.raises(SpeechError, match="provider_failed"):
        service.generate(operation_id, request_with())
    receipt = service.inspect(operation_id)
    assert receipt["status"] == "failed"
    assert len(receipt["child_operations"]) == 1
    assert len(receipt["retained_inputs"]) == 1
    with pytest.raises(MovieError, match="operation_incomplete"):
        service.generate(operation_id, request_with())
    assert assets.calls == ["preflight", "image", "narration"]


@pytest.mark.parametrize(
    "filename",
    ["scene-00.image.png", "scene-00.narration.wav", "render.mp4", "thumbnail.png"],
)
def test_inspection_verifies_every_retained_asset(tmp_path, operation_id, filename):
    service = MovieService(
        tmp_path / "state", RecordingAssets(tmp_path), RecordingAssembler()
    )
    service.generate(operation_id, request_with())
    (service.operation_directory(operation_id) / filename).write_bytes(b"changed")
    with pytest.raises(MovieError, match="asset_checksum_mismatch"):
        service.inspect(operation_id)


def test_incomplete_input_manifest_is_not_a_successful_receipt(tmp_path, operation_id):
    service = MovieService(
        tmp_path / "state", RecordingAssets(tmp_path), RecordingAssembler()
    )
    receipt = service.generate(operation_id, request_with())
    receipt["retained_inputs"] = [receipt["retained_inputs"][0]] * 2
    (service.operation_directory(operation_id) / "receipt.json").write_text(
        json.dumps(receipt)
    )
    with pytest.raises(MovieError, match="invalid_receipt"):
        service.inspect(operation_id)
