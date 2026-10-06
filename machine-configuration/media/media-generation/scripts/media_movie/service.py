import hashlib
import json
import time
from dataclasses import asdict

from media_image.contract import validate_operation_id
from media_movie.asset_files import describe_movie_outputs
from media_movie.scene_generation import prepare_movie_scenes
from media_movie.contract import (
    MovieAssembler,
    MovieAssetGenerator,
    MovieError,
)
from media_movie.receipts import inspect_movie_receipt
from media_video.files import atomic_json, create_private_directory


class MovieService:
    def __init__(
        self, state_directory, assets: MovieAssetGenerator, assembler: MovieAssembler
    ):
        self.state_directory = state_directory.expanduser().absolute()
        self.assets = assets
        self.assembler = assembler

    def operation_directory(self, operation_id):
        validate_operation_id(operation_id)
        return self.state_directory / operation_id

    def inspect(self, operation_id):
        return inspect_movie_receipt(
            self.operation_directory(operation_id), operation_id
        )

    def completed_operation(self, operation_id, digest):
        receipt = self.inspect(operation_id)
        if receipt["request_sha256"] != digest:
            raise MovieError("operation_conflict")
        if receipt["status"] != "succeeded":
            raise MovieError("operation_incomplete")
        return receipt

    def generate(self, operation_id, request):
        directory = self.operation_directory(operation_id)
        digest = hashlib.sha256(
            json.dumps(
                {"assembler": self.assembler.name, **asdict(request)},
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
        ).hexdigest()
        if directory.exists():
            return self.completed_operation(operation_id, digest)
        self.assembler.preflight(request)
        for scene in request.scenes:
            self.assets.preflight(scene)
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
            "assembler": self.assembler.name,
            "child_operations": [],
            "retained_inputs": [],
            "receipt_path": str(directory / "receipt.json"),
            "cost": {
                "currency": "USD",
                "provider_charge_usd": None,
                "status": "unknown",
                "budget_reserved": False,
            },
        }
        atomic_json(directory / "receipt.json", receipt)
        try:
            scenes = prepare_movie_scenes(
                operation_id, request, directory, receipt, self.assets
            )
            result = self.assembler.assemble(request, tuple(scenes), directory)
            assets = describe_movie_outputs(directory)
            receipt.update(
                status="succeeded",
                media=result["media"],
                verification=result["verification"],
                assets=assets,
                elapsed_seconds=time.monotonic() - started,
            )
            atomic_json(directory / "receipt.json", receipt)
            receipt = self.inspect(operation_id)
        except BaseException as error:
            receipt.update(
                status="failed",
                error=getattr(error, "category", "movie_failed"),
                elapsed_seconds=time.monotonic() - started,
            )
            atomic_json(directory / "receipt.json", receipt)
            raise
        return receipt
