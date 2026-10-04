import base64
import binascii

from media_speech.contract import (
    CharacterAlignment,
    SpeechError,
    SpeechRequest,
    SynthesizedSpeech,
)


class ElevenLabsSpeechProvider:
    name = "elevenlabs"
    model = "eleven_multilingual_v2"
    requires_payment = True

    def __init__(self, api_key: str | None, client=None):
        self.api_key = api_key
        self.client = client

    def preflight(self, request: SpeechRequest):
        if not self.api_key:
            raise SpeechError("missing_credentials")

    def synthesize(self, request: SpeechRequest):
        from elevenlabs.client import ElevenLabs
        from elevenlabs.core.api_error import ApiError

        client = self.client or ElevenLabs(api_key=self.api_key, timeout=120)
        try:
            response = client.text_to_speech.with_raw_response.convert_with_timestamps(
                request.voice,
                text=request.text,
                model_id=self.model,
                language_code=request.language.split("-")[0],
                output_format="pcm_24000",
                request_options={"max_retries": 0},
            )
        except ApiError as error:
            categories = {
                401: "authentication_failed",
                402: "insufficient_balance",
                403: "permission_denied",
                422: "provider_rejected_request",
                429: "rate_limited",
            }
            raise SpeechError(
                categories.get(error.status_code, "provider_failed")
            ) from None
        try:
            data = response.data
            pcm_audio = base64.b64decode(data.audio_base_64, validate=True)
            alignment = None
            if data.alignment is not None:
                alignment = CharacterAlignment(
                    tuple(data.alignment.characters),
                    tuple(data.alignment.character_start_times_seconds),
                    tuple(data.alignment.character_end_times_seconds),
                )
            character_cost = response.headers.get("character-cost")
            billed_characters = None
            if character_cost is not None:
                try:
                    billed_characters = int(character_cost)
                except ValueError:
                    raise SpeechError("invalid_usage") from None
                if billed_characters < 0:
                    raise SpeechError("invalid_usage")
            return SynthesizedSpeech(
                pcm_audio,
                24000,
                alignment,
                response.headers.get("request-id"),
                billed_characters,
            )
        except (binascii.Error, ValueError, AttributeError):
            raise SpeechError("invalid_provider_response") from None
        finally:
            response.close()
