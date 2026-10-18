import json
import subprocess
import uuid

import pytest

from agent_api.contract import CapabilityError, OperationRequest
from agent_api.providers.media import MediaProvider
from agent_api.providers.processing import ProcessingProvider
from agent_api.service import CapabilityService


def test_real_worker_probes_audio_and_replays_without_reprocessing(tmp_path):
    import wave

    audio = tmp_path / "input.wav"
    with wave.open(str(audio), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b"\x00\x00" * 16000)
    service = CapabilityService(tmp_path / "state")
    operation_id = str(uuid.uuid4())
    request = OperationRequest("media.probe", {"path": str(audio)}, 30)
    result = service.run(operation_id, request)
    assert result["status"] == "succeeded"
    assert result["result"]["output"]["streams"][0]["sample_rate"] == "16000"
    assert result == service.run(operation_id, request)


def test_media_adapter_records_child_identity_before_failure(tmp_path, monkeypatch):
    def fail(*args):
        assert (
            json.loads((tmp_path / "submission.json").read_text())["operation_id"]
            == "child-id"
        )
        raise CapabilityError("tool_failed")

    monkeypatch.setattr("agent_api.providers.media.run_tool", fail)
    request = OperationRequest(
        "image.generate",
        {
            "provider": "openai",
            "prompt": "cat",
            "model": "model",
            "aspect_ratio": "1:1",
            "quality": "low",
        },
        allow_paid=True,
    )
    with pytest.raises(CapabilityError, match="tool_failed"):
        MediaProvider().execute(request, tmp_path, "child-id")


def test_media_adapter_retains_nested_movie_assets(tmp_path):
    source = tmp_path / "source.mp4"
    source.write_bytes(b"retained")
    output = tmp_path / "output"
    output.mkdir()
    receipt = {"assets": {"video": {"path": str(source)}}}
    MediaProvider().retain_artifacts(receipt, output)
    assert (output / "video.mp4").read_bytes() == b"retained"


def test_local_processors_use_arguments_without_a_shell(tmp_path, monkeypatch):
    source = tmp_path / "input ; literal.wav"
    source.write_bytes(b"audio")
    calls = []

    def run(arguments, **options):
        calls.append((arguments, options))
        options["stdout"].write(b'{"streams": []}')
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr("agent_api.providers.processing.subprocess.run", run)
    request = OperationRequest("media.probe", {"path": str(source)})
    assert ProcessingProvider().execute(request, tmp_path, "operation")["streams"] == []
    assert calls[0][0][-1] == str(source)
    assert "shell" not in calls[0][1]
