import os
from pathlib import Path

from media_image.contract import ImageError
from media_image.openai_provider import OpenAIImageProvider
from media_image.replicate_provider import ReplicateImageProvider


def read_credential(environment_name, filename):
    credential = os.environ.get(environment_name)
    if credential:
        return credential
    try:
        return (Path.home() / ".secrets" / filename).read_text(
            encoding="utf-8"
        ).strip() or None
    except FileNotFoundError:
        return None


def create_image_provider(provider_name):
    if provider_name == "openai":
        return OpenAIImageProvider(read_credential("OPENAI_API_KEY", "openai-api-key"))
    if provider_name == "replicate":
        return ReplicateImageProvider(
            read_credential("REPLICATE_API_TOKEN", "replicate-api-token")
        )
    raise ImageError("unsupported_provider")
