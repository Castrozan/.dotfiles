DEFAULT_MODEL = "veo"

MODEL_REGISTRY = {
    "veo": {
        "repository": "veo-3.1-generate-preview",
        "provider": "gemini-veo",
        "defaults": {
            "aspect_ratio": "16:9",
            "resolution": "1080p",
            "duration_seconds": 8,
        },
        "description": "Google Veo 3.1 via the Gemini API, frontier-quality coherent T2V with audio; PAID tier, needs GEMINI_API_KEY, ~$0.40/s (8s 1080p ~ $3.20)",
    },
    "veo-fast": {
        "repository": "veo-3.1-fast-generate-preview",
        "provider": "gemini-veo",
        "defaults": {
            "aspect_ratio": "16:9",
            "resolution": "1080p",
            "duration_seconds": 8,
        },
        "description": "Google Veo 3.1 Fast via the Gemini API, cheaper coherent T2V; PAID tier, needs GEMINI_API_KEY, ~$0.12/s (8s 1080p ~ $0.96)",
    },
    "sora-pro": {
        "repository": "sora-2-pro",
        "provider": "openai-sora",
        "defaults": {
            "duration_seconds": 8,
            "size": "1280x720",
        },
        "description": "OpenAI Sora 2 Pro via the OpenAI API, coherent T2V; PAID, needs OPENAI_API_KEY, ~$0.70/s (8s ~ $5.60); API sunsets 2026-09-24",
    },
    "sora": {
        "repository": "sora-2",
        "provider": "openai-sora",
        "defaults": {
            "duration_seconds": 8,
            "size": "1280x720",
        },
        "description": "OpenAI Sora 2 via the OpenAI API, coherent T2V; PAID, needs OPENAI_API_KEY, ~$0.30/s (8s ~ $2.40); API sunsets 2026-09-24",
    },
}

HOSTED_PROVIDERS = {"gemini-veo", "openai-sora"}


def print_model_registry():
    for name in sorted(MODEL_REGISTRY.keys()):
        spec = MODEL_REGISTRY[name]
        marker = " (default)" if name == DEFAULT_MODEL else ""
        print(f"{name}{marker}: {spec['description']}")
        print(f"    repository: {spec['repository']}")
