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
from media_speech.delivery import direct_speech_text, speech_model_capabilities


def read_elevenlabs_api_key():
    environment_key = os.environ.get("ELEVENLABS_API_KEY")
    if environment_key:
        return environment_key
    credential_path = Path.home() / ".secrets" / "elevenlabs-api-key"
    try:
        return credential_path.read_text(encoding="utf-8").strip() or None
    except FileNotFoundError:
        return None


def describe_speech_providers():
    return {
        "providers": [
            {
                **asdict(provider.describe()),
                "models": speech_model_capabilities(provider.name),
                "usage": asdict(ProviderUsageService(reader).capabilities()),
            }
            for provider, reader in (
                (KokoroSpeechProvider, KokoroUsageReader()),
                (ElevenLabsSpeechProvider, ElevenLabsUsageReader(None)),
            )
        ]
    }


def read_speech_request(args):
    text = args.text
    if args.text_file is not None:
        with args.text_file.open(encoding="utf-8") as input_file:
            text = input_file.read(MAXIMUM_TEXT_CHARACTERS + 1)
    text = direct_speech_text(text, args.provider, args.model, args.directions)
    return SpeechRequest(text, args.voice, args.language)


def create_speech_provider(args):
    if args.provider == "elevenlabs":
        return ElevenLabsSpeechProvider(read_elevenlabs_api_key(), model=args.model)
    if args.model is not None and args.model != KokoroSpeechProvider.model:
        raise SpeechError("unsupported_model")
    return KokoroSpeechProvider(
        Path(os.environ["MEDIA_KOKORO_MODEL"]),
        Path(os.environ["MEDIA_KOKORO_VOICES"]),
        Path(os.environ["MEDIA_ESPEAK_LIBRARY"]),
        Path(os.environ["MEDIA_ESPEAK_DATA"]),
    )


def generate_speech(args, service):
    request = read_speech_request(args)
    provider = create_speech_provider(args)
    if args.command == "validate":
        provider.preflight(request)
        return {"status": "valid", "provider": provider.name, "model": provider.model}
    operation_id = args.operation_id or str(uuid.uuid4())
    print(json.dumps({"operation_id": operation_id}), file=sys.stderr, flush=True)
    return service.generate(operation_id, request, provider)


def list_speech_voices(args):
    query = VoiceQuery(args.page_size, args.page_token, args.search)
    catalog: SpeechVoiceCatalog = (
        ElevenLabsSpeechProvider(read_elevenlabs_api_key())
        if args.provider == "elevenlabs"
        else KokoroVoiceCatalog()
    )
    return {"provider": args.provider, **asdict(catalog.list_voices(query))}


def read_speech_usage(provider_name):
    reader = (
        ElevenLabsUsageReader(read_elevenlabs_api_key())
        if provider_name == "elevenlabs"
        else KokoroUsageReader()
    )
    return asdict(ProviderUsageService(reader).read_usage())


def execute_speech_command(args):
    if args.command == "providers":
        return describe_speech_providers()
    if args.command == "voices":
        return list_speech_voices(args)
    if args.command == "usage":
        return read_speech_usage(args.provider)
    service = SpeechService(args.state_directory.expanduser().absolute())
    if args.command == "inspect":
        return service.inspect(args.operation_id)
    return generate_speech(args, service)


def main(arguments=None):
    args = build_parser().parse_args(arguments)
    try:
        receipt = execute_speech_command(args)
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
