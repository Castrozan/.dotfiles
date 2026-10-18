from agent_api.catalogs.local import capability, text


def media_capabilities():
    return [
        capability(
            "image.generate",
            "media",
            "Generate one PNG through the existing media-image API and retain its child receipt.",
            {
                "provider": {"enum": ["openai", "replicate"]},
                "model": text(100),
                "prompt": text(8000),
                "aspect_ratio": {"enum": ["1:1", "2:3", "3:2", "9:16", "16:9"]},
                "quality": text(20),
                "seed": {"type": "integer", "minimum": 0, "maximum": 2147483647},
            },
            ["provider", "model", "prompt", "aspect_ratio", "quality"],
            "provider_plan",
        ),
        capability(
            "speech.generate",
            "media",
            "Generate local Kokoro or cloud ElevenLabs speech through media-speech.",
            {
                "provider": {"enum": ["kokoro", "elevenlabs"]},
                "model": text(100),
                "text": text(4000),
                "voice": text(100),
                "language": {"enum": ["pt-br", "en-us"]},
                "directions": text(1000),
            },
            ["provider", "text", "voice", "language"],
            "speech_provider",
        ),
        capability(
            "movie.generate",
            "media",
            "Assemble explicit generated image and narration scenes through media-movie; inspect schema first.",
            {"request": {"type": "object"}},
            ["request"],
            "provider_plan",
        ),
        capability(
            "video.render",
            "media",
            "Render a trusted registered native recipe through media-video.",
            {"request": {"type": "object"}},
            ["request"],
        ),
        capability(
            "media.providers",
            "media",
            "Read models and controls for an existing media API without generating anything.",
            {"kind": {"enum": ["image", "speech", "movie"]}},
            ["kind"],
        ),
        capability(
            "movie.schema",
            "media",
            "Read the existing movie scene request JSON Schema.",
            {},
            [],
        ),
    ]
