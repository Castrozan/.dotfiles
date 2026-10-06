import base64
import io
import sys

import httpx
from PIL import Image

import media_image_cli
import media_speech_cli
from media_image.openai_provider import OpenAIImageProvider
from media_speech.elevenlabs_provider import ElevenLabsSpeechProvider


def fixture_response(request):
    if request.url.path.endswith("/images/generations"):
        output = io.BytesIO()
        Image.new("RGB", (64, 64), "purple").save(output, format="PNG")
        return httpx.Response(
            200,
            headers={"x-request-id": "fixture-image"},
            json={
                "created": 1,
                "data": [{"b64_json": base64.b64encode(output.getvalue()).decode()}],
            },
        )
    return httpx.Response(
        200,
        headers={"request-id": "fixture-speech"},
        json={
            "audio_base64": base64.b64encode(b"\x00\x01" * 4800).decode(),
            "alignment": None,
            "normalized_alignment": None,
        },
    )


def main():
    kind = sys.argv.pop(1)
    with httpx.Client(transport=httpx.MockTransport(fixture_response)) as transport:
        if kind == "image":
            from openai import OpenAI

            client = OpenAI(
                api_key="fixture-only", http_client=transport, max_retries=0
            )
            media_image_cli.create_image_provider = (
                lambda provider: OpenAIImageProvider("fixture-only", client)
            )
            return media_image_cli.main()
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key="fixture-only", httpx_client=transport)
        media_speech_cli.ElevenLabsSpeechProvider = (
            lambda api_key, model=None: ElevenLabsSpeechProvider(
                "fixture-only", client, model
            )
        )
        return media_speech_cli.main()


if __name__ == "__main__":
    raise SystemExit(main())
