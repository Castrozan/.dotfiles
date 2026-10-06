import base64
from contextlib import ExitStack

from media_image.contract import MAXIMUM_IMAGE_BYTES, ImageError
from media_image.discovery import OPENAI_SIZES, validate_provider_request
from media_image.image_decoder import decode_generated_image


def decode_openai_document(document, provider_request_id):
    try:
        image_bytes = read_openai_image_bytes(document)
        usage = read_openai_image_usage(document)
        return decode_generated_image(image_bytes, provider_request_id, usage)
    except (ValueError, TypeError, AttributeError):
        raise ImageError("invalid_provider_response") from None


def read_openai_image_bytes(document):
    if len(document.data or []) != 1:
        raise ImageError("invalid_provider_response")
    encoded_image = document.data[0].b64_json
    return decode_openai_base64_image(encoded_image)


def decode_openai_base64_image(encoded_image):
    if not isinstance(encoded_image, str) or len(encoded_image) > 4 * (
        (MAXIMUM_IMAGE_BYTES + 2) // 3
    ):
        raise ImageError("invalid_provider_response")
    return base64.b64decode(encoded_image, validate=True)


def read_openai_image_usage(document):
    reported_usage = getattr(document, "usage", None)
    reported = {} if reported_usage is None else reported_usage.model_dump()
    usage = {
        key: reported[key]
        for key in ("input_tokens", "output_tokens", "total_tokens")
        if reported.get(key) is not None
    }
    return usage or None


def request_openai_image(client, request, record_submission):
    from openai import APIConnectionError, APIStatusError, APITimeoutError

    try:
        return client.images.with_raw_response.generate(
            model=request.model,
            prompt=request.prompt,
            size=OPENAI_SIZES[request.aspect_ratio],
            quality=request.quality,
            output_format="png",
            n=1,
        )
    except APITimeoutError:
        raise ImageError("provider_timeout") from None
    except APIConnectionError:
        raise ImageError("provider_unavailable") from None
    except APIStatusError as error:
        record_openai_error(error, record_submission)


def record_openai_error(error, record_submission):
    if error.request_id:
        record_submission(error.request_id)
    categories = {
        401: "authentication_failed",
        402: "insufficient_balance",
        403: "permission_denied",
        429: "rate_limited",
    }
    raise ImageError(categories.get(error.status_code, "provider_failed")) from None


class OpenAIImageProvider:
    name = "openai"

    def __init__(self, api_key, client=None):
        self.api_key = api_key
        self.client = client

    def preflight(self, request):
        validate_provider_request(self.name, request)
        if not self.api_key:
            raise ImageError("missing_credentials")

    def generate(self, request, record_submission):
        from openai import OpenAI

        with ExitStack() as resources:
            client = self.client
            if client is None:
                client = resources.enter_context(
                    OpenAI(api_key=self.api_key, max_retries=0, timeout=180)
                )
            response = request_openai_image(client, request, record_submission)
            resources.callback(response.http_response.close)
            provider_request_id = response.headers.get("x-request-id")
            if provider_request_id:
                record_submission(provider_request_id)
            return decode_openai_document(response.parse(), provider_request_id)
