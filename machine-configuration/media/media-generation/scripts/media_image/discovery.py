from media_image.contract import MAXIMUM_PROMPT_CHARACTERS, ImageError

OPENAI_MODELS = ("gpt-image-2.5-flare", "gpt-image-2.5-sunburst", "gpt-image-1-mini")
REPLICATE_MODELS = ("black-forest-labs/flux-schnell",)
OPENAI_SIZES = {"1:1": "1024x1024", "2:3": "1024x1536", "3:2": "1536x1024"}


def describe_image_providers():
    return {
        "providers": [
            {
                "provider": "openai",
                "execution": "cloud",
                "requires_payment": True,
                "requires_credentials": True,
                "credential_environment": "OPENAI_API_KEY",
                "credential_file": "openai-api-key",
                "operations": ["text_to_image"],
                "output_formats": ["png"],
                "maximum_prompt_characters": MAXIMUM_PROMPT_CHARACTERS,
                "models": [
                    {
                        "model": model,
                        "aspect_ratios": list(OPENAI_SIZES),
                        "qualities": ["low", "medium", "high"]
                        + ([] if model == "gpt-image-1-mini" else ["xhigh", "max"]),
                        "seed": False,
                        "delivery_instructions": "prompt",
                        "usage": "reported_tokens",
                        "pricing_url": "https://developers.openai.com/api/docs/guides/image-generation",
                    }
                    for model in OPENAI_MODELS
                ],
                "account_usage": {
                    "status": "unavailable",
                    "scope": "account",
                    "metrics": [],
                },
            },
            {
                "provider": "replicate",
                "execution": "cloud",
                "requires_payment": True,
                "requires_credentials": True,
                "credential_environment": "REPLICATE_API_TOKEN",
                "credential_file": "replicate-api-token",
                "operations": ["text_to_image"],
                "output_formats": ["png"],
                "maximum_prompt_characters": MAXIMUM_PROMPT_CHARACTERS,
                "models": [
                    {
                        "model": REPLICATE_MODELS[0],
                        "aspect_ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
                        "qualities": ["standard"],
                        "seed": True,
                        "delivery_instructions": "prompt",
                        "usage": "reported_predict_seconds",
                        "weights_license": "Apache-2.0",
                        "pricing_url": "https://replicate.com/black-forest-labs/flux-schnell",
                    }
                ],
                "account_usage": {
                    "status": "unavailable",
                    "scope": "account",
                    "metrics": [],
                },
            },
        ]
    }


def provider_model(provider_name, model_name):
    provider = next(
        (
            entry
            for entry in describe_image_providers()["providers"]
            if entry["provider"] == provider_name
        ),
        None,
    )
    if provider is None:
        raise ImageError("unsupported_provider")
    model = next(
        (entry for entry in provider["models"] if entry["model"] == model_name), None
    )
    if model is None:
        raise ImageError("unsupported_model")
    return model


def validate_provider_request(provider_name, request):
    model = provider_model(provider_name, request.model)
    if request.aspect_ratio not in model["aspect_ratios"]:
        raise ImageError("unsupported_aspect_ratio")
    if request.quality not in model["qualities"]:
        raise ImageError("unsupported_quality")
    if request.seed is not None and not model["seed"]:
        raise ImageError("unsupported_seed")
