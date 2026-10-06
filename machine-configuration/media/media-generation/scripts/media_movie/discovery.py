from media_image.discovery import describe_image_providers
from media_speech.delivery import speech_model_capabilities


def describe_movie_providers():
    return {
        "provider": "ffmpeg",
        "execution": "local_assembly_with_provider_asset_jobs",
        "operations": ["scene_script_to_mp4", "inspect", "successful_replay"],
        "output": {
            "video": "video/mp4",
            "video_codec": "h264",
            "audio_codec": "aac",
            "thumbnail": "image/png",
        },
        "formats": {
            "minimum_dimension": 16,
            "maximum_dimension": 1920,
            "dimension_multiple": 2,
            "fps": [24, 25, 30],
            "maximum_duration_seconds": 600,
        },
        "script": {
            "minimum_scenes": 1,
            "maximum_scenes": 24,
            "maximum_narration_characters": 8000,
            "scene_motion": ["static", "zoom_in"],
            "captions": "not_assembled",
            "music": "not_assembled",
        },
        "image_providers": describe_image_providers()["providers"],
        "speech_providers": [
            {"provider": provider, "models": speech_model_capabilities(provider)}
            for provider in ("kokoro", "elevenlabs")
        ],
        "cost": {
            "provider_charge": "unknown_until_reconciled",
            "budget_reservation": False,
            "compute_cost": "not_measured",
        },
    }


def example_movie_request():
    return {
        "experiment_id": "shorts",
        "episode_id": "mountain-story",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "scenes": [
            {
                "image": {
                    "provider": "replicate",
                    "model": "black-forest-labs/flux-schnell",
                    "prompt": "A mountain at dawn, editorial paper collage, bold silhouettes, room for titles",
                    "aspect_ratio": "9:16",
                    "quality": "standard",
                    "seed": 42,
                },
                "narration": {
                    "provider": "elevenlabs",
                    "model": "eleven_v4",
                    "voice": "YOUR_VOICE_ID",
                    "language": "en-us",
                    "text": "It started with a mountain. Then the climb began.",
                    "directions": "curious, then quietly determined",
                },
                "motion": "zoom_in",
            }
        ],
    }
