import argparse
import json
import os
import sys
from pathlib import Path

from media_video.contract import VideoError, VideoRequest, validate_operation_id
from media_video.fframes import FframesRenderer
from media_video.files import read_json
from media_video.service import VideoService


def build_parser():
    parser = argparse.ArgumentParser(
        description="Render native fframes recipes with durable video receipts."
    )
    parser.add_argument(
        "--state-directory",
        type=Path,
        default=Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
        / "media-video",
        help="Private operation receipts, retained inputs, logs and rendered artifacts.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    render = commands.add_parser(
        "render", help="Render or replay a checksum-pinned recipe."
    )
    render.add_argument("--request-file", type=Path, required=True)
    inspect = commands.add_parser(
        "inspect", help="Read a receipt and verify its retained artifacts."
    )
    inspect.add_argument("operation_id")
    return parser


def main(arguments=None):
    args = build_parser().parse_args(arguments)
    service = VideoService(args.state_directory.expanduser().absolute())
    try:
        if args.command == "inspect":
            result = service.inspect(args.operation_id)
        else:
            document = read_json(args.request_file.expanduser().absolute())
            operation_id = validate_operation_id(document.pop("operation_id", None))
            try:
                request = VideoRequest(**document)
            except TypeError:
                raise VideoError("invalid_request") from None
            result = service.render(operation_id, request, FframesRenderer())
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
        return 0
    except VideoError as error:
        print(json.dumps({"error": error.category}), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    except (OSError, UnicodeError):
        print(json.dumps({"error": "storage_failed"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
