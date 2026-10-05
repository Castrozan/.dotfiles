from dataclasses import asdict
from pathlib import Path

from media_video.contract import (
    VideoError,
    VideoRenderProvider,
    VideoRequest,
    validate_operation_id,
)
from media_video.deadline import ExecutionDeadline
from media_video.files import (
    atomic_json,
    create_private_directory,
    file_digest,
    private_directory,
    read_json,
    sync_directory,
    sync_file,
    valid_digest,
)
from media_video.inputs import preserve_inputs, request_digest, verify_retained_inputs


class VideoService:
    def __init__(self, state_directory: Path):
        self.state_directory = state_directory

    def operation_directory(self, operation_id):
        return self.state_directory / validate_operation_id(operation_id)

    def inspect(self, operation_id):
        directory = self.operation_directory(operation_id)
        try:
            private_directory(self.state_directory)
            private_directory(directory)
            receipt = read_json(directory / "receipt.json", private=True)
        except FileNotFoundError:
            if directory.exists():
                raise VideoError("operation_incomplete") from None
            raise VideoError("operation_unavailable") from None
        if (
            receipt.get("operation_id") != operation_id
            or not isinstance(receipt.get("status"), str)
            or receipt.get("status") not in {"dispatching", "succeeded", "failed"}
            or not valid_digest(receipt.get("request_sha256"))
        ):
            raise VideoError("invalid_receipt")
        if receipt["status"] == "succeeded":
            verify_retained_inputs(directory, receipt.get("retained_inputs"))
            assets = receipt.get("assets")
            if not isinstance(assets, dict) or set(assets) != {"video", "thumbnail"}:
                raise VideoError("invalid_receipt")
            for name, filename in (
                ("video", "render.mp4"),
                ("thumbnail", "thumbnail.png"),
            ):
                asset = assets[name]
                path = directory / filename
                if not isinstance(asset, dict) or asset.get("path") != str(path):
                    raise VideoError("invalid_receipt")
                try:
                    if file_digest(path) != asset.get("sha256"):
                        raise VideoError("asset_checksum_mismatch")
                except FileNotFoundError:
                    raise VideoError("asset_unavailable") from None
        return receipt

    def completed_operation(self, operation_id, digest):
        receipt = self.inspect(operation_id)
        if receipt["request_sha256"] != digest:
            raise VideoError("operation_conflict")
        if receipt["status"] != "succeeded":
            raise VideoError("operation_incomplete")
        return receipt

    def render(
        self, operation_id: str, request: VideoRequest, renderer: VideoRenderProvider
    ):
        directory = self.operation_directory(operation_id)
        deadline = ExecutionDeadline(request.deadline_seconds)
        recipe = renderer.preflight(request, deadline)
        digest = request_digest(request, recipe, renderer)
        if directory.exists():
            return self.completed_operation(operation_id, digest)
        create_private_directory(self.state_directory)
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            return self.completed_operation(operation_id, digest)
        sync_directory(self.state_directory)
        receipt = {
            "operation_id": operation_id,
            "status": "dispatching",
            "request_sha256": digest,
            "request": asdict(request),
            "recipe_id": recipe.recipe_id,
            "renderer": renderer.name,
            "renderer_version": recipe.renderer_version,
            "adapter_version": renderer.adapter_version,
            "receipt_path": str(directory / "receipt.json"),
            "retained_inputs": [],
            "logs_directory": str(directory / "logs"),
            "cost": {
                "generative_provider_calls": 0,
                "generative_provider_charge_usd": 0,
                "scope": "local_render_only",
                "compute_cost_usd": None,
                "compute_cost_status": "not_measured",
            },
        }
        atomic_json(directory / "receipt.json", receipt)
        try:
            atomic_json(
                directory / "request.json",
                {"operation_id": operation_id, **asdict(request)},
            )
            prepared, retained = preserve_inputs(recipe, directory, deadline)
            receipt["retained_inputs"] = retained
            atomic_json(directory / "receipt.json", receipt)
            result = renderer.render(request, prepared, directory, deadline)
            verify_retained_inputs(directory, retained, deadline)
            assets = {}
            for name, filename, mime in (
                ("video", "render.mp4", "video/mp4"),
                ("thumbnail", "thumbnail.png", "image/png"),
            ):
                path = directory / filename
                assets[name] = {
                    "path": str(path),
                    "mime_type": mime,
                    "size_bytes": path.stat().st_size,
                    "sha256": file_digest(path, deadline),
                }
                sync_file(path)
            deadline.remaining()
            receipt.update(
                status="succeeded",
                media=result.media,
                verification=result.verification,
                assets=assets,
                elapsed_seconds=deadline.elapsed(),
            )
            atomic_json(directory / "receipt.json", receipt)
        except BaseException as error:
            category = (
                error.category if isinstance(error, VideoError) else "render_failed"
            )
            receipt.update(
                status="failed", error=category, elapsed_seconds=deadline.elapsed()
            )
            atomic_json(directory / "receipt.json", receipt)
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            raise VideoError(category) from None
        return receipt
