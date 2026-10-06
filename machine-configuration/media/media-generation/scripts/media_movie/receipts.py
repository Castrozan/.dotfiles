import json
import re

from media_movie.asset_files import asset_checksum
from media_movie.contract import MovieError


def read_movie_receipt(directory):
    path = directory / "receipt.json"
    try:
        if any(
            (
                directory.is_symlink(),
                path.is_symlink(),
                path.stat().st_size > 1024 * 1024,
            )
        ):
            raise MovieError("invalid_receipt")
        return json.loads(path.read_bytes())
    except FileNotFoundError:
        raise MovieError("operation_unavailable") from None
    except (OSError, ValueError):
        raise MovieError("invalid_receipt") from None


def validate_movie_receipt(receipt, operation_id):
    if not isinstance(receipt, dict):
        raise MovieError("invalid_receipt")
    if any(
        (
            receipt.get("operation_id") != operation_id,
            receipt.get("status") not in ("dispatching", "succeeded", "failed"),
        )
    ):
        raise MovieError("invalid_receipt")
    digest = receipt.get("request_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise MovieError("invalid_receipt")


def verify_scene_manifest(directory, inputs, scenes):
    validate_scene_manifest_shape(inputs, scenes)
    for asset in inputs:
        verify_scene_asset(directory, asset)
    expected = expected_scene_filenames(len(scenes))
    if (
        len(inputs) != len(expected)
        or {asset["filename"] for asset in inputs} != expected
    ):
        raise MovieError("invalid_receipt")


def validate_scene_manifest_shape(inputs, scenes):
    if not isinstance(inputs, list) or not isinstance(scenes, list):
        raise MovieError("invalid_receipt")
    if not 1 <= len(scenes) <= 24 or not 2 <= len(inputs) <= 48:
        raise MovieError("invalid_receipt")


def expected_scene_filenames(scene_count):
    return {
        f"scene-{index:02}.{suffix}"
        for index in range(scene_count)
        for suffix in ("image.png", "narration.wav")
    }


def verify_scene_asset(directory, asset):
    if not isinstance(asset, dict) or not isinstance(asset.get("filename"), str):
        raise MovieError("invalid_receipt")
    if not re.fullmatch(
        r"scene-\d{2}\.(image\.png|narration\.wav)", asset["filename"], re.ASCII
    ):
        raise MovieError("invalid_receipt")
    verify_asset(directory, asset["filename"], asset)


def verify_movie_outputs(directory, assets):
    if not isinstance(assets, dict) or set(assets) != {"video", "thumbnail"}:
        raise MovieError("invalid_receipt")
    verify_asset(directory, "render.mp4", assets["video"])
    verify_asset(directory, "thumbnail.png", assets["thumbnail"])


def inspect_movie_receipt(directory, operation_id):
    receipt = read_movie_receipt(directory)
    validate_movie_receipt(receipt, operation_id)
    if receipt["status"] != "succeeded":
        return receipt
    document = receipt.get("request")
    if not isinstance(document, dict):
        raise MovieError("invalid_receipt")
    verify_scene_manifest(
        directory, receipt.get("retained_inputs"), document.get("scenes")
    )
    verify_movie_outputs(directory, receipt.get("assets"))
    return receipt


def verify_asset(directory, filename, asset):
    if not isinstance(asset, dict):
        raise MovieError("invalid_receipt")
    digest = asset.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise MovieError("invalid_receipt")
    if asset_checksum(directory / filename) != digest:
        raise MovieError("asset_checksum_mismatch")
