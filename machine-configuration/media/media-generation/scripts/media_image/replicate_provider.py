import asyncio
from contextlib import AsyncExitStack

import httpx

from media_image.contract import ImageError
from media_image.discovery import validate_provider_request
from media_image.image_decoder import decode_generated_image
from media_image.replicate_assets import download_replicate_image


def replicate_arguments(request):
    arguments = {
        "prompt": request.prompt,
        "aspect_ratio": request.aspect_ratio,
        "num_outputs": 1,
        "num_inference_steps": 4,
        "output_format": "png",
    }
    if request.seed is not None:
        arguments["seed"] = request.seed
    return arguments


async def request_replicate_prediction(client, request, record_submission):
    prediction = await client.predictions.async_create(
        model=request.model, input=replicate_arguments(request)
    )
    if not isinstance(prediction.id, str) or not 1 <= len(prediction.id) <= 200:
        raise ImageError("invalid_provider_response")
    record_submission(prediction.id)
    while prediction.status not in ("succeeded", "failed", "canceled"):
        await asyncio.sleep(1)
        await prediction.async_reload()
    if prediction.status != "succeeded":
        raise ImageError("provider_failed")
    return prediction


async def decode_replicate_prediction(prediction, download_client):
    if not isinstance(prediction.output, list) or len(prediction.output) != 1:
        raise ImageError("invalid_provider_response")
    image_bytes = await download_replicate_image(prediction.output[0], download_client)
    reported = prediction.metrics or {}
    usage = {
        key: reported[key]
        for key in ("predict_time", "total_time")
        if reported.get(key) is not None
    }
    return decode_generated_image(image_bytes, prediction.id, usage)


class ReplicateImageProvider:
    name = "replicate"

    def __init__(self, api_key, client=None, download_client=None):
        self.api_key = api_key
        self.client = client
        self.download_client = download_client

    def preflight(self, request):
        validate_provider_request(self.name, request)
        if not self.api_key:
            raise ImageError("missing_credentials")

    def generate(self, request, record_submission):
        try:
            return asyncio.run(
                asyncio.wait_for(
                    self.generate_async(request, record_submission), timeout=180
                )
            )
        except TimeoutError:
            raise ImageError("provider_timeout") from None

    async def generate_async(self, request, record_submission):
        async with AsyncExitStack() as resources:
            client = self.client
            if client is None:
                from replicate import Client

                transport = await resources.enter_async_context(
                    httpx.AsyncHTTPTransport(retries=0)
                )
                client = Client(
                    api_token=self.api_key,
                    base_url="https://api.replicate.com",
                    timeout=httpx.Timeout(30),
                    transport=transport,
                )
            downloads = self.download_client
            if downloads is None:
                downloads = await resources.enter_async_context(
                    httpx.AsyncClient(timeout=30, trust_env=False)
                )
            return await self.request_and_decode(
                client, downloads, request, record_submission
            )

    async def request_and_decode(self, client, downloads, request, record_submission):
        from replicate.exceptions import ReplicateError

        try:
            prediction = await request_replicate_prediction(
                client, request, record_submission
            )
            return await decode_replicate_prediction(prediction, downloads)
        except ReplicateError as error:
            categories = {
                401: "authentication_failed",
                402: "insufficient_balance",
                403: "permission_denied",
                429: "rate_limited",
            }
            raise ImageError(categories.get(error.status, "provider_failed")) from None
        except httpx.TimeoutException:
            raise ImageError("provider_timeout") from None
        except httpx.HTTPError:
            raise ImageError("provider_unavailable") from None
        except (ValueError, TypeError, AttributeError):
            raise ImageError("invalid_provider_response") from None
