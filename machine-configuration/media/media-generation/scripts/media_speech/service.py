import hashlib
import json
import resource
import sys
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from media_speech import receipts
from media_speech.audio_assets import (
    describe_alignment,
    describe_audio,
    validate_synthesized_speech,
    write_speech_wave,
)
from media_speech.contract import SpeechError, SpeechProvider, SpeechRequest


def load_receipt(directory: Path):
    try:
        return json.loads(
            (directory / receipts.RECEIPT_FILENAME).read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        raise SpeechError("operation_unavailable") from None
    except (ValueError, OSError):
        raise SpeechError("invalid_receipt") from None


def validate_receipt_envelope(receipt, operation_id: str):
    if (
        not isinstance(receipt, dict)
        or receipt.get("operation_id") != operation_id
        or receipt.get("status") not in {"dispatching", "succeeded", "failed"}
        or not isinstance(receipt.get("request_sha256"), str)
    ):
        raise SpeechError("invalid_receipt")


def verify_succeeded_audio(directory: Path, receipt):
    if not isinstance(receipt.get("audio"), dict) or not isinstance(
        receipt["audio"].get("sha256"), str
    ):
        raise SpeechError("invalid_receipt")
    try:
        digest = hashlib.sha256((directory / "speech.wav").read_bytes()).hexdigest()
    except OSError:
        raise SpeechError("asset_unavailable") from None
    if digest != receipt["audio"]["sha256"]:
        raise SpeechError("asset_checksum_mismatch")


def compute_request_digest(provider: SpeechProvider, request: SpeechRequest):
    return hashlib.sha256(
        json.dumps(
            {"provider": provider.name, "model": provider.model, **asdict(request)},
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def build_dispatching_receipt(
    directory: Path,
    operation_id: str,
    request_digest: str,
    provider: SpeechProvider,
    request: SpeechRequest,
):
    return {
        "operation_id": operation_id,
        "status": "dispatching",
        "request_sha256": request_digest,
        "provider": provider.name,
        "model": provider.model,
        "voice": request.voice,
        "language": request.language,
        "input_characters": len(request.text),
        "cost": {
            "currency": "USD",
            "provider_charge": None if provider.requires_payment else 0,
            "status": "unknown" if provider.requires_payment else "no_provider_charge",
        },
        "receipt_path": str(directory / receipts.RECEIPT_FILENAME),
    }


def peak_process_memory_bytes():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if sys.platform == "darwin" else 1024
    )


def failure_category(error: BaseException):
    if isinstance(error, SpeechError):
        return error.category
    return "generation_failed"


def record_failed_operation(directory: Path, receipt, started: float, category: str):
    receipt.update(
        status="failed",
        error=category,
        elapsed_seconds=time.monotonic() - started,
    )
    receipts.write_receipt(directory, receipt)


class SpeechService:
    def __init__(self, state_directory: Path):
        self.state_directory = state_directory

    def operation_directory(self, operation_id: str):
        try:
            if str(uuid.UUID(operation_id)) != operation_id:
                raise ValueError
        except ValueError:
            raise SpeechError("invalid_operation_id") from None
        return self.state_directory / operation_id

    def inspect(self, operation_id: str):
        directory = self.operation_directory(operation_id)
        receipt = load_receipt(directory)
        validate_receipt_envelope(receipt, operation_id)
        if receipt["status"] == "succeeded":
            verify_succeeded_audio(directory, receipt)
        return receipt

    def generate(
        self, operation_id: str, request: SpeechRequest, provider: SpeechProvider
    ):
        directory = self.operation_directory(operation_id)
        request_digest = compute_request_digest(provider, request)
        if directory.exists():
            return self.completed_operation(operation_id, request_digest)
        provider.preflight(request)
        self.state_directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            return self.completed_operation(operation_id, request_digest)
        receipt = build_dispatching_receipt(
            directory, operation_id, request_digest, provider, request
        )
        receipts.write_receipt(directory, receipt)
        started = time.monotonic()
        try:
            speech = provider.synthesize(request)
            receipt.update(
                provider_request_id=speech.provider_request_id,
                billed_characters=speech.billed_characters,
                alignment_adjustments=list(speech.alignment_adjustments),
            )
            duration = validate_synthesized_speech(speech)
            audio_path = directory / "speech.wav"
            write_speech_wave(audio_path, speech)
            receipt.update(
                status="succeeded",
                audio=describe_audio(audio_path, speech, duration),
                alignment=describe_alignment(speech.alignment, request.text),
                elapsed_seconds=time.monotonic() - started,
                peak_process_memory_bytes=peak_process_memory_bytes(),
            )
            receipts.write_receipt(directory, receipt)
        except BaseException as error:
            category = failure_category(error)
            record_failed_operation(directory, receipt, started, category)
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            raise SpeechError(category) from None
        return receipt

    def completed_operation(self, operation_id: str, request_digest: str):
        try:
            receipt = self.inspect(operation_id)
        except SpeechError as error:
            if error.category == "operation_unavailable":
                raise SpeechError("operation_incomplete") from None
            raise
        if receipt["request_sha256"] != request_digest:
            raise SpeechError("operation_conflict")
        if receipt["status"] != "succeeded":
            raise SpeechError("operation_incomplete")
        return receipt
