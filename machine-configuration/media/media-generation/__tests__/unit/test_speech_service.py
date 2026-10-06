import json
import threading
import wave
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from media_speech.contract import SpeechError
from media_speech.service import SpeechService


def test_success_owns_measured_audio_and_replays_without_generation(
    tmp_path, speech_request, operation_id, provider_factory
):
    service = SpeechService(tmp_path / "jobs")
    provider = provider_factory()
    receipt = service.generate(operation_id, speech_request, provider)
    assert receipt["status"] == "succeeded"
    assert receipt["audio"]["duration_seconds"] == 1
    assert receipt["audio"]["size_bytes"] == 48044
    assert receipt["alignment"] == {"status": "unavailable"}
    assert receipt["cost"]["provider_charge"] == 0
    with wave.open(receipt["audio"]["path"]) as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (
            1,
            2,
            24000,
        )
        assert audio.getnframes() == 24000
    assert service.generate(operation_id, speech_request, provider) == receipt
    assert provider.calls == 1
    assert (tmp_path / "jobs" / operation_id).stat().st_mode & 0o777 == 0o700


def test_interruption_before_first_receipt_cannot_dispatch_again(
    tmp_path, speech_request, operation_id, provider_factory
):
    (tmp_path / operation_id).mkdir()
    provider = provider_factory()
    service = SpeechService(tmp_path)
    with pytest.raises(SpeechError, match="operation_incomplete"):
        service.generate(operation_id, speech_request, provider)
    assert provider.calls == 0


@pytest.mark.parametrize("contents", ["[]", "{}", "broken JSON"])
def test_invalid_receipt_is_reported_consistently(tmp_path, operation_id, contents):
    directory = tmp_path / operation_id
    directory.mkdir()
    (directory / "receipt.json").write_text(contents)
    service = SpeechService(tmp_path)
    with pytest.raises(SpeechError, match="invalid_receipt"):
        service.inspect(operation_id)


def test_same_operation_with_different_text_is_a_conflict(
    tmp_path, speech_request, operation_id, provider_factory
):
    service = SpeechService(tmp_path)
    provider = provider_factory()
    service.generate(operation_id, speech_request, provider)
    conflicting_request = replace(speech_request, text="Different")
    with pytest.raises(SpeechError, match="operation_conflict"):
        service.generate(operation_id, conflicting_request, provider)
    assert provider.calls == 1


def test_corrupted_owned_asset_cannot_be_replayed(
    tmp_path, speech_request, operation_id, provider_factory
):
    service = SpeechService(tmp_path)
    provider = provider_factory()
    receipt = service.generate(operation_id, speech_request, provider)
    (tmp_path / operation_id / "speech.wav").write_bytes(b"corrupted")
    with pytest.raises(SpeechError, match="asset_checksum_mismatch"):
        service.generate(operation_id, speech_request, provider)
    assert receipt["status"] == "succeeded"
    assert provider.calls == 1


@pytest.mark.parametrize("error", [TimeoutError("secret value"), KeyboardInterrupt()])
def test_uncertain_paid_failure_stays_unknown_and_is_never_retried(
    tmp_path, speech_request, operation_id, error, provider_factory
):
    service = SpeechService(tmp_path)
    provider = provider_factory(error=error)
    provider.requires_payment = True
    with pytest.raises((SpeechError, KeyboardInterrupt)):
        service.generate(operation_id, speech_request, provider)
    receipt = service.inspect(operation_id)
    assert receipt["status"] == "failed"
    assert receipt["cost"] == {
        "currency": "USD",
        "provider_charge": None,
        "status": "unknown",
    }
    assert "secret value" not in json.dumps(receipt)
    with pytest.raises(SpeechError, match="operation_incomplete"):
        service.generate(operation_id, speech_request, provider)
    assert provider.calls == 1


def test_concurrent_same_operation_dispatches_only_once(
    tmp_path, speech_request, operation_id, provider_factory
):
    entered = threading.Event()
    release = threading.Event()
    provider = provider_factory()
    original_synthesize = provider.synthesize

    def blocked_synthesize(speech_request):
        entered.set()
        assert release.wait(5)
        return original_synthesize(speech_request)

    provider.synthesize = blocked_synthesize
    service = SpeechService(tmp_path)
    with ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(
            service.generate, operation_id, speech_request, provider
        )
        assert entered.wait(5)
        try:
            with pytest.raises(SpeechError, match="operation_incomplete"):
                service.generate(operation_id, speech_request, provider)
        finally:
            release.set()
        assert first.result()["status"] == "succeeded"
    assert provider.calls == 1
