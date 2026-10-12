import hashlib
import json
import os
import resource
import sys
import time
import uuid
import wave
from dataclasses import asdict
from pathlib import Path

from media_speech import receipts
from media_speech.contract import SpeechError, SpeechProvider, SpeechRequest


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
        try:
            receipt = json.loads(
                (directory / receipts.RECEIPT_FILENAME).read_text(encoding="utf-8")
            )
        except FileNotFoundError:
            raise SpeechError("operation_unavailable") from None
        except (ValueError, OSError):
            raise SpeechError("invalid_receipt") from None
        if (
            not isinstance(receipt, dict)
            or receipt.get("operation_id") != operation_id
            or receipt.get("status") not in {"dispatching", "succeeded", "failed"}
            or not isinstance(receipt.get("request_sha256"), str)
        ):
            raise SpeechError("invalid_receipt")
        if receipt["status"] == "succeeded":
            if not isinstance(receipt.get("audio"), dict) or not isinstance(
                receipt["audio"].get("sha256"), str
            ):
                raise SpeechError("invalid_receipt")
            try:
                digest = hashlib.sha256(
                    (directory / "speech.wav").read_bytes()
                ).hexdigest()
            except OSError:
                raise SpeechError("asset_unavailable") from None
            if digest != receipt["audio"]["sha256"]:
                raise SpeechError("asset_checksum_mismatch")
        return receipt

    def generate(
        self, operation_id: str, request: SpeechRequest, provider: SpeechProvider
    ):
        directory = self.operation_directory(operation_id)
        request_digest = hashlib.sha256(
            json.dumps(
                {"provider": provider.name, "model": provider.model, **asdict(request)},
                sort_keys=True,
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        if directory.exists():
            return self.completed_operation(operation_id, request_digest)
        provider.preflight(request)
        self.state_directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            return self.completed_operation(operation_id, request_digest)
        receipt = {
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
                "status": "unknown"
                if provider.requires_payment
                else "no_provider_charge",
            },
            "receipt_path": str(directory / receipts.RECEIPT_FILENAME),
        }
        receipts.write_receipt(directory, receipt)
        started = time.monotonic()
        try:
            speech = provider.synthesize(request)
            receipt.update(
                provider_request_id=speech.provider_request_id,
                billed_characters=speech.billed_characters,
                alignment_adjustments=list(speech.alignment_adjustments),
            )
            if speech.sample_rate_hz != 24000:
                raise SpeechError("invalid_sample_rate")
            if (
                not speech.pcm_audio
                or len(speech.pcm_audio) % 2
                or len(speech.pcm_audio) > 24000 * 2 * 600
            ):
                raise SpeechError("invalid_audio")
            duration = len(speech.pcm_audio) / (speech.sample_rate_hz * 2)
            if speech.alignment is not None:
                speech.alignment.validate(duration)
            audio_path = directory / "speech.wav"
            with audio_path.open("xb") as output:
                with wave.open(output, "wb") as audio:
                    audio.setnchannels(1)
                    audio.setsampwidth(2)
                    audio.setframerate(speech.sample_rate_hz)
                    audio.writeframes(speech.pcm_audio)
                output.flush()
                os.fsync(output.fileno())
            receipt.update(
                status="succeeded",
                audio={
                    "path": str(audio_path),
                    "mime_type": "audio/wav",
                    "encoding": "pcm_s16le",
                    "sample_rate_hz": speech.sample_rate_hz,
                    "channels": 1,
                    "duration_seconds": duration,
                    "size_bytes": audio_path.stat().st_size,
                    "sha256": hashlib.sha256(audio_path.read_bytes()).hexdigest(),
                },
                alignment=(
                    {
                        "status": "available",
                        "granularity": "character",
                        "text_matches_input": "".join(speech.alignment.characters)
                        == request.text,
                        **asdict(speech.alignment),
                    }
                    if speech.alignment is not None
                    else {"status": "unavailable"}
                ),
                elapsed_seconds=time.monotonic() - started,
                peak_process_memory_bytes=resource.getrusage(
                    resource.RUSAGE_SELF
                ).ru_maxrss
                * (1 if sys.platform == "darwin" else 1024),
            )
            receipts.write_receipt(directory, receipt)
        except BaseException as error:
            category = (
                error.category
                if isinstance(error, SpeechError)
                else "generation_failed"
            )
            receipt.update(
                status="failed",
                error=category,
                elapsed_seconds=time.monotonic() - started,
            )
            receipts.write_receipt(directory, receipt)
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
