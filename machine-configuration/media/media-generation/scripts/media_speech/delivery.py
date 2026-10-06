from media_speech.contract import SpeechError


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


def direct_speech_text(text, provider_name, model, directions):
    if directions is None:
        return text
    if provider_name != "elevenlabs" or model != "eleven_v4":
        raise SpeechError("unsupported_delivery_instructions")
    validate_delivery_directions(directions)
    return f"[{directions.strip()}] {text}"


def validate_delivery_directions(directions):
    if not isinstance(directions, str):
        raise SpeechError("invalid_delivery_instructions")
    if not 1 <= len(directions.strip()) <= 200:
        raise SpeechError("invalid_delivery_instructions")
    if any(invalid_delivery_character(character) for character in directions):
        raise SpeechError("invalid_delivery_instructions")


def invalid_delivery_character(character):
    return character in "[]" or ord(character) < 32
