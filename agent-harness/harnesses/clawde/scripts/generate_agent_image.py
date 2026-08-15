"""Generate one image into the calling agent's workspace and print its path.

The path is what the channel plugin's reply tool attaches. With no reference the
prompt is drawn from scratch; with references the model edits what the channel
already downloaded, which is how "draw one like the picture they just posted"
works.
"""

import argparse
import base64
import sys
from datetime import date
from pathlib import Path

from agent_media_transport import post_json, post_multipart
from agent_media_workspace import (
    MediaRequestRefused,
    claim_daily_allowance,
    flatten_prompt,
    read_api_key,
    resolve_media_directory,
    resolve_reference_file,
    write_media_file,
)

GENERATIONS_URL = "https://api.openai.com/v1/images/generations"
EDITS_URL = "https://api.openai.com/v1/images/edits"
MODEL = "gpt-image-1-mini"
SECRET_NAME = "openai-api-key"
QUALITIES = ("low", "medium", "high")
SIZES = ("1024x1024", "1024x1536", "1536x1024")
PROMPT_LENGTH_LIMIT = 1200
DAILY_LIMIT = 24
MAXIMUM_REFERENCES = 4


def parse_command_line_arguments(argv):
    parser = argparse.ArgumentParser(
        prog="clawde-agent-image-generate",
        description="Generate one image into this agent's own media directory.",
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        help="Path to an image the channel downloaded, to edit instead of drawing from scratch. Repeatable.",
    )
    parser.add_argument("--quality", choices=QUALITIES, default="low")
    parser.add_argument("--size", choices=SIZES, default="1024x1024")
    return parser.parse_args(argv)


def request_drawn_image(api_key, prompt, quality, size):
    return post_json(
        GENERATIONS_URL,
        {"authorization": f"Bearer {api_key}"},
        {
            "model": MODEL,
            "prompt": prompt,
            "quality": quality,
            "size": size,
            "n": 1,
        },
    )


def request_edited_image(api_key, prompt, quality, size, reference_files):
    return post_multipart(
        EDITS_URL,
        {"authorization": f"Bearer {api_key}"},
        {"model": MODEL, "prompt": prompt, "quality": quality, "size": size, "n": "1"},
        [("image[]", path) for path in reference_files],
    )


def decode_image(reported):
    entries = reported.get("data") or []
    if not entries or "b64_json" not in entries[0]:
        raise MediaRequestRefused("the media provider returned no image")
    return base64.b64decode(entries[0]["b64_json"])


def generate_agent_image(working_directory, arguments, today):
    media_directory = resolve_media_directory(working_directory)
    prompt = flatten_prompt(arguments.prompt, PROMPT_LENGTH_LIMIT)
    if len(arguments.reference) > MAXIMUM_REFERENCES:
        raise MediaRequestRefused(
            f"refusing more than {MAXIMUM_REFERENCES} reference images"
        )
    reference_files = [
        resolve_reference_file(reference, media_directory)
        for reference in arguments.reference
    ]
    api_key = read_api_key(SECRET_NAME)
    claim_daily_allowance(media_directory, "image", DAILY_LIMIT, today)
    if reference_files:
        reported = request_edited_image(
            api_key, prompt, arguments.quality, arguments.size, reference_files
        )
    else:
        reported = request_drawn_image(
            api_key, prompt, arguments.quality, arguments.size
        )
    return write_media_file(media_directory, "image", ".png", decode_image(reported))


def main(argv=None):
    arguments = parse_command_line_arguments(sys.argv[1:] if argv is None else argv)
    try:
        media_file = generate_agent_image(Path.cwd(), arguments, date.today())
    except MediaRequestRefused as refusal:
        print(str(refusal), file=sys.stderr)
        return 1
    print(media_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
