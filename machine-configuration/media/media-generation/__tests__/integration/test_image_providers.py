import base64
import io
import json

import httpx
import pytest
from openai import OpenAI
from PIL import Image
from replicate import Client

from media_image.contract import ImageError, ImageRequest
from media_image.openai_provider import OpenAIImageProvider
from media_image.replicate_provider import ReplicateImageProvider


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


def test_replicate_sdk_preserves_prediction_and_downloads_without_credentials():
    requests = []
    download_requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(
            201,
            json={
                "id": "replicate-receipt",
                "model": "black-forest-labs/flux-schnell",
                "version": "fixture",
                "status": "succeeded",
                "input": {},
                "output": ["https://fixture.replicate.delivery/image.png"],
                "created_at": "2026-10-05T00:00:00Z",
                "metrics": {"predict_time": 0.25},
            },
        )

    def download(request):
        download_requests.append(request)
        return httpx.Response(200, content=image_bytes())

    client = Client(api_token="synthetic-only", transport=httpx.MockTransport(respond))
    download_client = httpx.AsyncClient(transport=httpx.MockTransport(download))
    provider = ReplicateImageProvider("synthetic-only", client, download_client)
    request = ImageRequest(
        "Apple", "black-forest-labs/flux-schnell", "9:16", "standard", 5
    )
    provider.preflight(request)
    submitted = []
    result = provider.generate(request, submitted.append)
    assert submitted == ["replicate-receipt"]
    assert len(requests) == 1
    assert (
        requests[0].url.path == "/v1/models/black-forest-labs/flux-schnell/predictions"
    )
    assert json.loads(requests[0].content)["input"] == {
        "prompt": "Apple",
        "aspect_ratio": "9:16",
        "num_outputs": 1,
        "num_inference_steps": 4,
        "output_format": "png",
        "seed": 5,
    }
    assert not download_requests[0].headers.get("authorization")
    assert result.usage == {"predict_time": 0.25}


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
            ReplicateImageProvider("synthetic-only"),
            ImageRequest("Apple", "black-forest-labs/flux-schnell", "1:1", "high"),
            "unsupported_quality",
        ),
    ],
)
def test_unsupported_controls_fail_before_dispatch(provider, image_request, category):
    with pytest.raises(ImageError, match=category):
        provider.preflight(image_request)
