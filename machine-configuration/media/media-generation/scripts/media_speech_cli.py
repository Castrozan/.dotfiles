import json
import os
import sys
import uuid
from dataclasses import asdict
from pathlib import Path

from media_speech.cli_arguments import build_parser
from media_speech.contract import MAXIMUM_TEXT_CHARACTERS, SpeechError, SpeechRequest
from media_speech.discovery import SpeechVoiceCatalog, VoiceQuery
from media_speech.elevenlabs_provider import ElevenLabsSpeechProvider
from media_speech.elevenlabs_usage import ElevenLabsUsageReader
from media_speech.kokoro_provider import KokoroSpeechProvider, KokoroVoiceCatalog
from media_speech.kokoro_usage import KokoroUsageReader
from media_speech.service import SpeechService
from media_speech.usage import ProviderUsageService


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
                    {
                        **asdict(provider.describe()),
                        "usage": asdict(ProviderUsageService(reader).capabilities()),
                    }
                    for provider, reader in (
                        (KokoroSpeechProvider, KokoroUsageReader()),
                        (ElevenLabsSpeechProvider, ElevenLabsUsageReader(None)),
                    )
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
        if args.command == "usage":
            reader = (
                ElevenLabsUsageReader(read_elevenlabs_api_key())
                if args.provider == "elevenlabs"
                else KokoroUsageReader()
            )
            result = asdict(ProviderUsageService(reader).read_usage())
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
