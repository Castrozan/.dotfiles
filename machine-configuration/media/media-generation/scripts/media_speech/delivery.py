from media_speech.contract import SpeechError

REGIONAL_ACCENT_CUES = {"pt-br": "strong Brazilian Portuguese accent"}


def speech_model_capabilities(provider_name):
    if provider_name == "elevenlabs":
        return [
            {
                "model": "eleven_multilingual_v2",
                "delivery_instructions": "text_and_ssml_breaks",
                "directions": False,
                "alignment": "character",
            },
            {
                "model": "eleven_v4",
                "delivery_instructions": "inline_audio_tags",
                "directions": True,
                "alignment": "character",
            },
            *[
                {
                    "model": model,
                    "delivery_instructions": "text",
                    "directions": False,
                    "alignment": "character",
                }
                for model in ("eleven_turbo_v2_5", "eleven_flash_v2_5")
            ],
        ]
    if provider_name == "kokoro":
        return [
            {
                "model": "kokoro-v1.0-int8-model-files-v1.0",
                "delivery_instructions": "text",
                "directions": False,
                "alignment": "unavailable",
            }
        ]
    raise SpeechError("unsupported_provider")


def supports_audio_tags(provider_name, model):
    return provider_name == "elevenlabs" and model == "eleven_v4"


def direct_speech_text(text, provider_name, model, directions, language):
    cues = [
        *direction_cues(provider_name, model, directions),
        *accent_cues(provider_name, model, language),
    ]
    if not cues:
        return text
    return f"[{', '.join(cues)}] {text}"


def direction_cues(provider_name, model, directions):
    if directions is None:
        return []
    if not supports_audio_tags(provider_name, model):
        raise SpeechError("unsupported_delivery_instructions")
    validate_delivery_directions(directions)
    return [directions.strip()]


def accent_cues(provider_name, model, language):
    if not supports_audio_tags(provider_name, model):
        return []
    if language not in REGIONAL_ACCENT_CUES:
        return []
    return [REGIONAL_ACCENT_CUES[language]]


def validate_delivery_directions(directions):
    if not isinstance(directions, str):
        raise SpeechError("invalid_delivery_instructions")
    if not 1 <= len(directions.strip()) <= 200:
        raise SpeechError("invalid_delivery_instructions")
    if any(invalid_delivery_character(character) for character in directions):
        raise SpeechError("invalid_delivery_instructions")


def invalid_delivery_character(character):
    return character in "[]" or ord(character) < 32
