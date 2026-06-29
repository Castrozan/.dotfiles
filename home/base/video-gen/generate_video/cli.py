import argparse
import os
import sys

from .models import DEFAULT_MODEL, MODEL_REGISTRY, print_model_registry


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="video-gen",
        description="Generate a video clip from a text prompt using a hosted video-generation API.",
    )
    parser.add_argument(
        "prompt", nargs="?", help="text description of the clip to generate"
    )
    parser.add_argument(
        "--model",
        choices=sorted(MODEL_REGISTRY.keys()),
        default=DEFAULT_MODEL,
        help=f"hosted model to call (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output", default="clip.mp4", help="output video path (default: clip.mp4)"
    )
    parser.add_argument(
        "--seconds", type=int, default=None, help="clip duration in seconds"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="print the available models and exit",
    )
    return parser.parse_args()


def main():
    arguments = parse_arguments()

    if arguments.list_models:
        print_model_registry()
        return 0

    if not arguments.prompt:
        print(
            "error: a text prompt is required (or pass --list-models)", file=sys.stderr
        )
        return 2

    model_spec = MODEL_REGISTRY[arguments.model]
    return run_hosted_generation(arguments, model_spec)


def run_hosted_generation(arguments, model_spec):
    from .hosted import (
        generate_with_gemini_veo,
        generate_with_openai_sora,
        resolve_gemini_api_key,
        resolve_openai_api_key,
    )

    provider = model_spec["provider"]
    if provider == "gemini-veo":
        api_key = resolve_gemini_api_key()
        key_hint = "set GEMINI_API_KEY or place it at ~/.secrets/gemini-api-key"
        generate = generate_with_gemini_veo
    else:
        api_key = resolve_openai_api_key()
        key_hint = "set OPENAI_API_KEY or place it at ~/.secrets/openai-api-key"
        generate = generate_with_openai_sora

    if not api_key:
        print(
            f"error: the {arguments.model} model needs an API key; {key_hint}. "
            "No request was sent, no spend.",
            file=sys.stderr,
        )
        return 2

    parameters = dict(model_spec["defaults"])
    if arguments.seconds is not None:
        parameters["duration_seconds"] = arguments.seconds

    output_path = os.path.abspath(arguments.output)
    print(f"model: {arguments.model} ({model_spec['repository']}) [hosted {provider}]")
    print(f"parameters: {parameters}")
    print("submitting to the hosted API (this is a paid request)...")
    generate(model_spec, arguments.prompt, parameters, output_path, api_key)
    print(f"wrote {output_path}")
    return 0
