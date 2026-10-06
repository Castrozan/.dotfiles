import hashlib
import json
import os
import time
from dataclasses import asdict
from pathlib import Path

from media_image.contract import (
    ImageError,
    ImageGenerationProvider,
    ImageRequest,
    validate_operation_id,
)
from media_image.receipts import inspect_image_receipt
from media_video.files import atomic_json, create_private_directory


class ImageService:
    def __init__(self, state_directory: Path):
        self.state_directory = state_directory.expanduser().absolute()

    def operation_directory(self, operation_id):
        validate_operation_id(operation_id)
        return self.state_directory / operation_id

    def inspect(self, operation_id):
        return inspect_image_receipt(
            self.operation_directory(operation_id), operation_id
        )

    def completed_operation(self, operation_id, request_digest):
        receipt = self.inspect(operation_id)
        if receipt["request_sha256"] != request_digest:
            raise ImageError("operation_conflict")
        if receipt["status"] != "succeeded":
            raise ImageError("operation_incomplete")
        return receipt

    def generate(
        self,
        operation_id: str,
        request: ImageRequest,
        provider: ImageGenerationProvider,
    ):
        directory = self.operation_directory(operation_id)
        digest = hashlib.sha256(
            json.dumps(
                {"provider": provider.name, **asdict(request)},
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
        ).hexdigest()
        if directory.exists():
            return self.completed_operation(operation_id, digest)
        provider.preflight(request)
        create_private_directory(self.state_directory)
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            return self.completed_operation(operation_id, digest)
        started = time.monotonic()
        receipt = {
            "operation_id": operation_id,
            "status": "dispatching",
            "request_sha256": digest,
            "request": asdict(request),
            "provider": provider.name,
            "model": request.model,
            "provider_request_id": None,
            "usage": None,
            "cost": {
                "currency": "USD",
                "provider_charge_usd": None,
                "status": "unknown",
                "budget_reserved": False,
            },
            "receipt_path": str(directory / "receipt.json"),
        }
        atomic_json(directory / "receipt.json", receipt)

        try:
            image = provider.generate(
                request,
                lambda identifier: record_image_submission(
                    directory, receipt, identifier
                ),
            )
            image_path = directory / "image.png"
            descriptor = os.open(
                image_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
            with os.fdopen(descriptor, "wb") as output:
                output.write(image.image_bytes)
                output.flush()
                os.fsync(output.fileno())
            receipt.update(
                status="succeeded",
                provider_request_id=image.provider_request_id
                or receipt["provider_request_id"],
                usage=image.usage,
                image={
                    "path": str(image_path),
                    "mime_type": "image/png",
                    "width": image.width,
                    "height": image.height,
                    "color_mode": image.color_mode,
                    "size_bytes": len(image.image_bytes),
                    "sha256": hashlib.sha256(image.image_bytes).hexdigest(),
                },
                elapsed_seconds=time.monotonic() - started,
            )
            atomic_json(directory / "receipt.json", receipt)
        except BaseException as error:
            receipt.update(
                status="failed",
                error=getattr(error, "category", "generation_failed"),
                elapsed_seconds=time.monotonic() - started,
            )
            atomic_json(directory / "receipt.json", receipt)
            raise
        return receipt


def record_image_submission(directory, receipt, provider_request_id):
    if (
        not isinstance(provider_request_id, str)
        or not 1 <= len(provider_request_id) <= 200
    ):
        raise ImageError("invalid_provider_response")
    receipt["provider_request_id"] = provider_request_id
    atomic_json(directory / "receipt.json", receipt)
