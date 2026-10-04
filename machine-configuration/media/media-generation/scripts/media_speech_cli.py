import argparse
import json
import os
import sys
import uuid
from pathlib import Path

from media_speech.contract import SpeechError, SpeechRequest
from media_speech.elevenlabs_provider import ElevenLabsSpeechProvider
from media_speech.kokoro_provider import KokoroSpeechProvider
from media_speech.service import SpeechService


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate file speech with durable receipts and explicit alignment support."
    )
    parser.add_argument(
        "--state-directory",
        type=Path,
        default=Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
        / "media-speech",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    generate = subcommands.add_parser("generate")
    generate.add_argument("--provider", required=True, choices=["kokoro", "elevenlabs"])
    generate.add_argument("--language", required=True, choices=["en-us", "pt-br"])
    generate.add_argument("--voice", required=True)
    generate.add_argument("--operation-id", default=None)
    text = generate.add_mutually_exclusive_group(required=True)
    text.add_argument("--text")
    text.add_argument("--text-file", type=Path)
    inspect = subcommands.add_parser("inspect")
    inspect.add_argument("operation_id")
    return parser


def main(arguments=None):
    args = build_parser().parse_args(arguments)
    service = SpeechService(args.state_directory.expanduser().absolute())
    try:
        if args.command == "inspect":
            receipt = service.inspect(args.operation_id)
        else:
            text = args.text
            if args.text_file is not None:
                with args.text_file.open(encoding="utf-8") as input_file:
                    text = input_file.read(4001)
            request = SpeechRequest(text, args.voice, args.language)
            if args.provider == "elevenlabs":
                provider = ElevenLabsSpeechProvider(
                    os.environ.get("ELEVENLABS_API_KEY")
                )
            else:
                provider = KokoroSpeechProvider(
                    Path(os.environ["MEDIA_KOKORO_MODEL"]),
                    Path(os.environ["MEDIA_KOKORO_VOICES"]),
                    Path(os.environ["MEDIA_ESPEAK_LIBRARY"]),
                    Path(os.environ["MEDIA_ESPEAK_DATA"]),
                )
            operation_id = args.operation_id or str(uuid.uuid4())
            print(
                json.dumps({"operation_id": operation_id}), file=sys.stderr, flush=True
            )
            receipt = service.generate(operation_id, request, provider)
        print(json.dumps(receipt, ensure_ascii=False, allow_nan=False, indent=2))
        return 0
    except SpeechError as error:
        print(json.dumps({"error": error.category}), file=sys.stderr)
        return 1
    except (OSError, UnicodeError):
        print(json.dumps({"error": "storage_failed"}), file=sys.stderr)
        return 1
    except KeyError:
        print(json.dumps({"error": "local_runtime_unavailable"}), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
