import hashlib
import json
import re

from media_image.contract import MAXIMUM_IMAGE_BYTES, ImageError


def read_image_receipt(directory):
    path = directory / "receipt.json"
    try:
        if any(
            (
                directory.is_symlink(),
                path.is_symlink(),
                path.stat().st_size > 1024 * 1024,
            )
        ):
            raise ImageError("invalid_receipt")
        return json.loads(path.read_bytes())
    except FileNotFoundError:
        raise ImageError("operation_unavailable") from None
    except (ValueError, OSError):
        raise ImageError("invalid_receipt") from None


def validate_image_receipt(receipt, operation_id):
    if not isinstance(receipt, dict):
        raise ImageError("invalid_receipt")
    if any(
        (
            receipt.get("operation_id") != operation_id,
            receipt.get("status") not in ("dispatching", "succeeded", "failed"),
        )
    ):
        raise ImageError("invalid_receipt")
    digest = receipt.get("request_sha256")
    validate_image_digest(digest)


def verify_retained_image(directory, image):
    if not isinstance(image, dict):
        raise ImageError("invalid_receipt")
    digest = image.get("sha256")
    validate_image_digest(digest)
    path = directory / "image.png"
    verify_image_checksum(path, digest)
    if image.get("path") != str(path) or image.get("size_bytes") != path.stat().st_size:
        raise ImageError("invalid_receipt")


def validate_image_digest(digest):
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ImageError("invalid_receipt")


def verify_image_checksum(path, digest):
    try:
        if any(
            (
                path.is_symlink(),
                not path.is_file(),
                not 0 < path.stat().st_size <= MAXIMUM_IMAGE_BYTES,
            )
        ):
            raise ImageError("asset_checksum_mismatch")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        raise ImageError("asset_unavailable") from None
    if actual != digest:
        raise ImageError("asset_checksum_mismatch")


def inspect_image_receipt(directory, operation_id):
    receipt = read_image_receipt(directory)
    validate_image_receipt(receipt, operation_id)
    if receipt["status"] == "succeeded":
        verify_retained_image(directory, receipt.get("image"))
    return receipt
