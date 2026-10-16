import argparse
import json
import sys
from pathlib import Path

from agent_media_workspace import MediaRequestRefused, resolve_media_directory

ATTACHMENT_TEXT_LIMIT_BYTES = 64 * 1024


def read_attachment(attachment, working_directory):
    workspace = resolve_media_directory(working_directory).parent
    inbox = (
        Path.home() / ".claude/channels/discord" / workspace.name / "inbox"
    ).resolve()
    path = Path(attachment).resolve(strict=True)
    if not path.is_relative_to(inbox) or not path.is_file():
        raise ValueError(
            "Attachment must be a saved file in this agent's Discord inbox"
        )
    with path.open("rb") as stream:
        payload = stream.read(ATTACHMENT_TEXT_LIMIT_BYTES + 1)
    if len(payload) > ATTACHMENT_TEXT_LIMIT_BYTES:
        raise ValueError("Attachment exceeds the 64 KiB text limit")
    text = payload.decode("utf-8-sig")
    if "\x00" in text:
        raise ValueError("Attachment must contain text")
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read a text attachment from this agent's Discord inbox (64 KiB maximum)."
    )
    parser.add_argument("attachment", type=Path)
    arguments = parser.parse_args(argv)
    try:
        text = read_attachment(arguments.attachment, Path.cwd())
    except (OSError, ValueError, MediaRequestRefused):
        print(
            "Cannot read this attachment; use a saved UTF-8 text file up to 64 KiB",
            file=sys.stderr,
        )
        return 1
    print(json.dumps({"text": text}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
