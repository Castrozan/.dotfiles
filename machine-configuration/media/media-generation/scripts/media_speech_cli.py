import argparse
import json
import os
import sys
import uuid
from dataclasses import asdict
from pathlib import Path

from media_speech.contract import (
    MAXIMUM_TEXT_CHARACTERS,
    SUPPORTED_LANGUAGES,
    SpeechError,
    SpeechRequest,
)
from media_speech.discovery import SpeechVoiceCatalog, VoiceQuery
from media_speech.elevenlabs_provider import ElevenLabsSpeechProvider
from media_speech.kokoro_provider import KokoroSpeechProvider, KokoroVoiceCatalog
from media_speech.service import SpeechService


def build_parser():
    parser = argparse.ArgumentParser(
        description="Discover speech providers and voices; generate audio with durable receipts."
    )
    parser.add_argument(
        "--state-directory",
        type=Path,
        default=Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
        / "media-speech",
        help="Directory for operation receipts and audio; replay is local to this directory.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser(
        "providers", help="Show configured models, languages and capabilities as JSON."
    )
    voices = subcommands.add_parser(
        "voices", help="List usable voice IDs without generating audio."
    )
    voices.add_argument("--provider", required=True, choices=["kokoro", "elevenlabs"])
    voices.add_argument(
        "--page-size",
        type=int,
        default=20,
        help="Requested page size, 1–100; default 20. ElevenLabs may add default voices.",
    )
    voices.add_argument(
        "--page-token",
        help="Continuation token returned by the previous page; keep the same search.",
    )
    voices.add_argument(
        "--search",
        help="Search voice names or IDs locally; account catalog fields on ElevenLabs.",
    )
    generate = subcommands.add_parser(
        "generate", help="Generate WAV audio or replay a successful operation."
    )
    generate.add_argument("--provider", required=True, choices=["kokoro", "elevenlabs"])
    generate.add_argument(
        "--language",
        required=True,
        choices=SUPPORTED_LANGUAGES,
        help="Requested narration language; see providers for language enforcement.",
    )
    generate.add_argument(
        "--voice",
        required=True,
        help="Use voice_id from 'media-speech voices --provider PROVIDER'.",
    )
    generate.add_argument(
        "--operation-id",
        default=None,
        help="Optional UUID; generated when omitted. Same UUID and request replay locally without generation; changed or failed operations cannot redispatch.",
    )
    text = generate.add_mutually_exclusive_group(required=True)
    text.add_argument(
        "--text",
        help=f"Narration text, at most {MAXIMUM_TEXT_CHARACTERS:,} characters.",
    )
    text.add_argument(
        "--text-file",
        type=Path,
        help="Read narration from a UTF-8 file with the same character limit.",
    )
    inspect = subcommands.add_parser(
        "inspect",
        help="Read an operation receipt and verify successful audio checksums.",
    )
    inspect.add_argument(
        "operation_id",
        help="UUID from a generation response; this is not a provider request ID.",
    )
    return parser


def read_elevenlabs_api_key():
    environment_key = os.environ.get("ELEVENLABS_API_KEY")
    if environment_key:
        return environment_key
    credential_path = Path.home() / ".secrets" / "elevenlabs-api-key"
    try:
        return credential_path.read_text(encoding="utf-8").strip() or None
    except FileNotFoundError:
        return None


def main(arguments=None):
    args = build_parser().parse_args(arguments)
    try:
        if args.command == "providers":
            result = {
                "providers": [
                    asdict(provider.describe())
                    for provider in (KokoroSpeechProvider, ElevenLabsSpeechProvider)
                ]
            }
            print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
            return 0
        if args.command == "voices":
            query = VoiceQuery(args.page_size, args.page_token, args.search)
            catalog: SpeechVoiceCatalog = (
                ElevenLabsSpeechProvider(read_elevenlabs_api_key())
                if args.provider == "elevenlabs"
                else KokoroVoiceCatalog()
            )
            result = {"provider": args.provider, **asdict(catalog.list_voices(query))}
            print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
            return 0
        service = SpeechService(args.state_directory.expanduser().absolute())
        if args.command == "inspect":
            receipt = service.inspect(args.operation_id)
        else:
            text = args.text
            if args.text_file is not None:
                with args.text_file.open(encoding="utf-8") as input_file:
                    text = input_file.read(MAXIMUM_TEXT_CHARACTERS + 1)
            request = SpeechRequest(text, args.voice, args.language)
            if args.provider == "elevenlabs":
                provider = ElevenLabsSpeechProvider(read_elevenlabs_api_key())
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
