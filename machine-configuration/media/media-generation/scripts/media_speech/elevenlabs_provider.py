import base64

from media_speech.elevenlabs_alignment import normalize_trailing_separators

from media_speech.contract import (
    CharacterAlignment,
    SpeechError,
    SpeechRequest,
    SynthesizedSpeech,
)
from media_speech.discovery import (
    SpeechCapabilities,
    SpeechVoice,
    SpeechVoicePage,
    VoiceQuery,
)


class ElevenLabsSpeechProvider:
    name = "elevenlabs"
    model = "eleven_multilingual_v2"
    requires_payment = True

    @classmethod
    def describe(cls):
        return SpeechCapabilities(
            cls.name,
            cls.model,
            "cloud",
            cls.requires_payment,
            True,
            "character",
            False,
            "account",
        )

    def __init__(self, api_key: str | None, client=None, model=None):
        self.api_key = api_key
        self.client = client
        self.model = model or type(self).model

    def preflight(self, request: SpeechRequest):
        if self.model not in ("eleven_multilingual_v2", "eleven_v4"):
            raise SpeechError("unsupported_model")
        if not self.api_key:
            raise SpeechError("missing_credentials")

    def list_voices(self, query: VoiceQuery):
        from elevenlabs.client import ElevenLabs
        from elevenlabs.core.api_error import ApiError
        from httpx import RequestError
        from pydantic import ValidationError

        if not self.api_key:
            raise SpeechError("missing_credentials")
        client = self.client or ElevenLabs(api_key=self.api_key, timeout=30)
        try:
            response = client.voices.search(
                page_size=query.page_size,
                next_page_token=query.page_token,
                search=query.search,
                request_options={"max_retries": 0},
            )
            if not isinstance(response.has_more, bool) or not isinstance(
                response.voices, list
            ):
                raise SpeechError("invalid_provider_response")
            if response.has_more and not response.next_page_token:
                raise SpeechError("invalid_provider_response")
            if response.has_more:
                VoiceQuery(page_token=response.next_page_token)
            return SpeechVoicePage(
                tuple(
                    SpeechVoice(
                        voice.voice_id,
                        voice.name or voice.voice_id,
                        preview_url=voice.preview_url,
                    )
                    for voice in response.voices
                ),
                response.next_page_token if response.has_more else None,
            )
        except ApiError as error:
            categories = {
                401: "authentication_failed",
                403: "permission_denied",
                429: "rate_limited",
            }
            raise SpeechError(
                categories.get(error.status_code, "provider_failed")
            ) from None
        except (ValidationError, ValueError, AttributeError, TypeError):
            raise SpeechError("invalid_provider_response") from None
        except SpeechError:
            raise SpeechError("invalid_provider_response") from None
        except RequestError:
            raise SpeechError("provider_unavailable") from None

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
            alignment, adjustments = normalize_trailing_separators(
                alignment, len(pcm_audio) / (24000 * 2)
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
                adjustments,
            )
        except (ValueError, AttributeError):
            raise SpeechError("invalid_provider_response") from None
        finally:
            response.close()
