import argparse
import json
import os
import sys
import uuid
from pathlib import Path

from media_image.contract import (
    MAXIMUM_PROMPT_CHARACTERS,
    SUPPORTED_ASPECT_RATIOS,
    ImageError,
    ImageRequest,
)
from media_image.discovery import describe_image_providers
from media_image.provider_factory import create_image_provider
from media_image.service import ImageService
from media_video.contract import VideoError


def build_parser():
    parser = argparse.ArgumentParser(
        description="Discover image providers and models; generate PNG assets with durable receipts."
    )
    parser.add_argument(
        "--state-directory",
        type=Path,
        default=Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
        / "media-image",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "providers",
        help="List models, supported controls, credential requirements and usage capabilities as JSON.",
    )
    generate = commands.add_parser(
        "generate",
        help="Generate one image or replay a successful operation without generating again.",
    )
    generate.add_argument("--provider", required=True, choices=("openai", "replicate"))
    generate.add_argument(
        "--model",
        required=True,
        help="Use a model ID from providers; models are validated before dispatch.",
    )
    generate.add_argument(
        "--aspect-ratio", required=True, choices=SUPPORTED_ASPECT_RATIOS
    )
    generate.add_argument(
        "--quality",
        required=True,
        help="Use a quality listed for the selected model in providers.",
    )
    generate.add_argument(
        "--seed",
        type=int,
        help="Optional deterministic seed; requires a model that advertises seed support.",
    )
    generate.add_argument(
        "--operation-id",
        help="Optional UUID; failed or interrupted operations cannot redispatch under this UUID.",
    )
    prompt = generate.add_mutually_exclusive_group(required=True)
    prompt.add_argument("--prompt")
    prompt.add_argument("--prompt-file", type=Path)
    commands.add_parser(
        "validate",
        parents=[generate],
        add_help=False,
        help="Validate the request and credential presence without generation or job state.",
    )
    inspect = commands.add_parser(
        "inspect", help="Inspect a local receipt and verify its retained PNG checksum."
    )
    inspect.add_argument("operation_id")
    return parser


def execute_image_command(args):
    if args.command == "providers":
        result = describe_image_providers()
    else:
        service = ImageService(args.state_directory.expanduser().absolute())
        if args.command == "inspect":
            result = service.inspect(args.operation_id)
        else:
            prompt = args.prompt
            if args.prompt_file is not None:
                with args.prompt_file.open(encoding="utf-8") as source:
                    prompt = source.read(MAXIMUM_PROMPT_CHARACTERS + 1)
            request = ImageRequest(
                prompt, args.model, args.aspect_ratio, args.quality, args.seed
            )
            provider = create_image_provider(args.provider)
            if args.command == "validate":
                provider.preflight(request)
                result = {
                    "status": "valid",
                    "provider": provider.name,
                    "model": request.model,
                }
            else:
                operation_id = args.operation_id or str(uuid.uuid4())
                print(
                    json.dumps({"operation_id": operation_id}),
                    file=sys.stderr,
                    flush=True,
                )
                result = service.generate(operation_id, request, provider)
    return result


def main(arguments=None):
    args = build_parser().parse_args(arguments)
    try:
        result = execute_image_command(args)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
        return 0
    except (ImageError, VideoError) as error:
        print(json.dumps({"error": error.category}), file=sys.stderr)
        return 1
    except (OSError, UnicodeError):
        print(json.dumps({"error": "storage_failed"}), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
