import io
import uuid

import pytest
from PIL import Image

from media_image.contract import GeneratedImage, ImageError, ImageRequest
from media_image.service import ImageService


class ImageFixtureProvider:
    name = "fixture"

    def __init__(self, error=None):
        self.calls = 0
        self.error = error

    def preflight(self, request):
        pass

    def generate(self, request, record_submission):
        self.calls += 1
        record_submission("fixture-submission")
        if self.error:
            raise self.error
        output = io.BytesIO()
        Image.new("RGB", (64, 64), "red").save(output, format="PNG")
        return GeneratedImage(output.getvalue(), 64, 64, "RGB", "fixture-submission")


@pytest.mark.parametrize("prompt", ["", " ", "x" * 8001, "bad\x00prompt"])
def test_invalid_prompt_is_rejected(prompt):
    with pytest.raises(ImageError, match="invalid_prompt"):
        ImageRequest(prompt, "fixture", "1:1", "standard")


def test_successful_replay_never_dispatches_again(tmp_path):
    service = ImageService(tmp_path)
    provider = ImageFixtureProvider()
    operation_id = str(uuid.uuid4())
    request = ImageRequest("An apple", "fixture", "1:1", "standard")
    receipt = service.generate(operation_id, request, provider)
    before = (tmp_path / operation_id / "image.png").stat().st_mtime_ns
    assert service.generate(operation_id, request, provider) == receipt
    assert service.inspect(operation_id) == receipt
    assert provider.calls == 1
    assert (tmp_path / operation_id / "image.png").stat().st_mtime_ns == before
    assert receipt["image"]["width"] == 64
    assert receipt["provider_request_id"] == "fixture-submission"
    assert receipt["cost"]["provider_charge_usd"] is None


def test_changed_request_conflicts(tmp_path):
    service = ImageService(tmp_path)
    provider = ImageFixtureProvider()
    operation_id = str(uuid.uuid4())
    service.generate(
        operation_id, ImageRequest("Apple", "fixture", "1:1", "standard"), provider
    )
    changed_request = ImageRequest("Pear", "fixture", "1:1", "standard")
    with pytest.raises(ImageError, match="operation_conflict"):
        service.generate(operation_id, changed_request, provider)
    assert provider.calls == 1


def test_failed_operation_keeps_submission_and_never_redispatches(tmp_path):
    service = ImageService(tmp_path)
    provider = ImageFixtureProvider(ImageError("provider_failed"))
    operation_id = str(uuid.uuid4())
    request = ImageRequest("Apple", "fixture", "1:1", "standard")
    with pytest.raises(ImageError, match="provider_failed"):
        service.generate(operation_id, request, provider)
    assert service.inspect(operation_id)["provider_request_id"] == "fixture-submission"
    with pytest.raises(ImageError, match="operation_incomplete"):
        service.generate(operation_id, request, provider)
    assert provider.calls == 1


def test_tampered_image_is_not_replayed(tmp_path):
    service = ImageService(tmp_path)
    provider = ImageFixtureProvider()
    operation_id = str(uuid.uuid4())
    request = ImageRequest("Apple", "fixture", "1:1", "standard")
    service.generate(operation_id, request, provider)
    (tmp_path / operation_id / "image.png").write_bytes(b"modified")
    with pytest.raises(ImageError, match="asset_checksum_mismatch"):
        service.generate(operation_id, request, provider)
    assert provider.calls == 1


@pytest.mark.parametrize(
    "operation_id", ["../escape", "bad", str(uuid.uuid4()).upper()]
)
def test_invalid_operation_id_does_not_dispatch(tmp_path, operation_id):
    provider = ImageFixtureProvider()
    service = ImageService(tmp_path)
    request = ImageRequest("Apple", "fixture", "1:1", "standard")
    with pytest.raises(ImageError, match="invalid_operation_id"):
        service.generate(operation_id, request, provider)
    assert provider.calls == 0
