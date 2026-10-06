import argparse
from pathlib import Path
import os

from media_speech.contract import MAXIMUM_TEXT_CHARACTERS, SUPPORTED_LANGUAGES


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
    usage = subcommands.add_parser(
        "usage",
        help="Read provider usage and quota information without generating audio.",
    )
    usage.add_argument("--provider", required=True, choices=["kokoro", "elevenlabs"])
    generate = subcommands.add_parser(
        "generate", help="Generate WAV audio or replay a successful operation."
    )
    generate.add_argument("--provider", required=True, choices=["kokoro", "elevenlabs"])
    generate.add_argument(
        "--model",
        help="Optional model ID from providers; the provider's existing default is used when omitted.",
    )
    generate.add_argument(
        "--directions",
        help="A delivery cue such as 'curious, then whispers'; requires ElevenLabs eleven_v4. Inline audio tags can also be placed in --text-file.",
    )
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
    subcommands.add_parser(
        "validate",
        parents=[generate],
        add_help=False,
        help="Validate narration, supported delivery controls and credential presence without synthesis or job state.",
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
