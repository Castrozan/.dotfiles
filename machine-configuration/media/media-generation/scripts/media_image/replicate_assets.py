from urllib.parse import urlsplit

from media_image.contract import MAXIMUM_IMAGE_BYTES, ImageError


def validate_replicate_asset_url(url):
    if not isinstance(url, str):
        raise ImageError("invalid_provider_response")
    try:
        parsed = urlsplit(url)
        invalid = any(
            (
                parsed.scheme != "https",
                bool(parsed.username),
                bool(parsed.password),
                parsed.port not in (None, 443),
            )
        )
    except ValueError:
        raise ImageError("invalid_asset_url") from None
    if invalid:
        raise ImageError("invalid_asset_url")
    hostname = parsed.hostname or ""
    if hostname != "replicate.delivery" and not hostname.endswith(
        ".replicate.delivery"
    ):
        raise ImageError("invalid_asset_url")


async def download_replicate_image(url, client):
    validate_replicate_asset_url(url)
    async with client.stream("GET", url, follow_redirects=False) as response:
        response.raise_for_status()
        parts = []
        size = 0
        async for part in response.aiter_bytes():
            size += len(part)
            if size > MAXIMUM_IMAGE_BYTES:
                raise ImageError("image_size_limit_exceeded")
            parts.append(part)
        return b"".join(parts)
