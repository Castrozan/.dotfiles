import base64
import io
import json

import httpx
import pytest
from openai import OpenAI
from PIL import Image

from media_image.contract import ImageError, ImageRequest
from media_image.openai_provider import OpenAIImageProvider


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (64, 96), "blue").save(output, format="PNG")
    return output.getvalue()


def test_official_openai_sdk_preserves_controls_receipt_and_usage():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(
            200,
            headers={"x-request-id": "openai-receipt"},
            json={
                "created": 1,
                "data": [{"b64_json": base64.b64encode(image_bytes()).decode()}],
                "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        with OpenAI(
            api_key="synthetic-only", max_retries=0, http_client=transport
        ) as client:
            provider = OpenAIImageProvider("synthetic-only", client)
            request = ImageRequest("An apple", "gpt-image-2.5-flare", "2:3", "high")
            provider.preflight(request)
            submitted = []
            result = provider.generate(request, submitted.append)
    assert len(requests) == 1
    assert requests[0].url.path == "/v1/images/generations"
    assert json.loads(requests[0].content) == {
        "model": "gpt-image-2.5-flare",
        "prompt": "An apple",
        "size": "1024x1536",
        "quality": "high",
        "output_format": "png",
        "n": 1,
    }
    assert result.width == 64
    assert result.height == 96
    assert result.usage == {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}
    assert submitted == ["openai-receipt"]


@pytest.mark.parametrize(
    "status,category",
    [
        (401, "authentication_failed"),
        (403, "permission_denied"),
        (429, "rate_limited"),
        (500, "provider_failed"),
    ],
)
def test_openai_error_does_not_submit_twice(status, category):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(
            status,
            json={"error": {"message": "Synthetic", "type": "synthetic", "code": None}},
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        with OpenAI(
            api_key="synthetic-only", max_retries=0, http_client=transport
        ) as client:
            provider = OpenAIImageProvider("synthetic-only", client)
            request = ImageRequest("Apple", "gpt-image-1-mini", "1:1", "low")
            with pytest.raises(ImageError, match=category):
                provider.generate(request, lambda _: None)
    assert len(requests) == 1


@pytest.mark.parametrize(
    "provider,image_request,category",
    [
        (
            OpenAIImageProvider(None),
            ImageRequest("Apple", "gpt-image-1-mini", "1:1", "low"),
            "missing_credentials",
        ),
        (
            OpenAIImageProvider("synthetic-only"),
            ImageRequest("Apple", "gpt-image-1-mini", "9:16", "low"),
            "unsupported_aspect_ratio",
        ),
        (
            OpenAIImageProvider("synthetic-only"),
            ImageRequest("Apple", "gpt-image-1-mini", "1:1", "low", 1),
            "unsupported_seed",
        ),
        (
            OpenAIImageProvider("synthetic-only"),
            ImageRequest("Apple", "gpt-image-1-mini", "1:1", "standard"),
            "unsupported_quality",
        ),
    ],
)
def test_unsupported_controls_fail_before_dispatch(provider, image_request, category):
    with pytest.raises(ImageError, match=category):
        provider.preflight(image_request)
