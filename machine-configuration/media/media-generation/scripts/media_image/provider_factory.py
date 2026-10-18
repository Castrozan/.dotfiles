import os
from pathlib import Path

from media_image.contract import ImageError
from media_image.openai_provider import OpenAIImageProvider


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
    raise ImageError("unsupported_provider")
