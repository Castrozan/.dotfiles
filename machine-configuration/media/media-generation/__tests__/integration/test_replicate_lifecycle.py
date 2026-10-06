import asyncio

import httpx
import pytest
from replicate import Client

from media_image.contract import ImageError, ImageRequest
from media_image.replicate_provider import ReplicateImageProvider
from media_image.replicate_assets import download_replicate_image


@pytest.mark.parametrize(
    "status,category",
    [
        (401, "authentication_failed"),
        (402, "insufficient_balance"),
        (403, "permission_denied"),
        (429, "rate_limited"),
        (500, "provider_failed"),
    ],
)
def test_replicate_paid_submission_is_never_retried(status, category):
    calls = []

    async def exercise():
        def respond(request):
            calls.append(request)
            return httpx.Response(status, json={"detail": "private provider response"})

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(respond)
        ) as downloads:
            client = Client(
                api_token="fixture-only", transport=httpx.MockTransport(respond)
            )
            provider = ReplicateImageProvider("fixture-only", client, downloads)
            request = ImageRequest(
                "Mountain", "black-forest-labs/flux-schnell", "1:1", "standard"
            )
            with pytest.raises(ImageError, match=category):
                await provider.generate_async(request, lambda identifier: None)
            await client._async_client.aclose()

    asyncio.run(exercise())
    assert len(calls) == 1
    assert calls[0].method == "POST"


@pytest.mark.parametrize(
    "url",
    [
        "http://replicate.delivery/image.png",
        "https://replicate.delivery.evil.example/image.png",
        "https://localhost/image.png",
        "https://name:secret@replicate.delivery/image.png",
        "https://replicate.delivery:123/image.png",
    ],
)
def test_output_download_refuses_untrusted_hosts_before_network_access(url):
    async def exercise():
        def respond(request):
            pytest.fail("untrusted asset URL reached transport")

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            with pytest.raises(ImageError, match="invalid_asset_url"):
                await download_replicate_image(url, client)

    asyncio.run(exercise())


def test_failed_prediction_keeps_its_remote_id_without_asset_download():
    submitted = []

    async def exercise():
        def respond(request):
            return httpx.Response(
                201,
                json={
                    "id": "failed-job",
                    "model": "black-forest-labs/flux-schnell",
                    "version": "fixture",
                    "status": "failed",
                    "error": "private provider failure",
                    "output": None,
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(respond)
        ) as downloads:
            client = Client(
                api_token="fixture-only", transport=httpx.MockTransport(respond)
            )
            provider = ReplicateImageProvider("fixture-only", client, downloads)
            request = ImageRequest(
                "Mountain", "black-forest-labs/flux-schnell", "1:1", "standard"
            )
            with pytest.raises(ImageError, match="provider_failed"):
                await provider.generate_async(request, submitted.append)
            await client._async_client.aclose()

    asyncio.run(exercise())
    assert submitted == ["failed-job"]
