import argparse
import json
import os
import sys
import uuid
from pathlib import Path

from media_image.contract import ImageError
from media_movie.asset_gateway import MovieAssetGateway
from media_movie.contract import MovieError
from media_movie.discovery import describe_movie_providers, example_movie_request
from media_movie.ffmpeg_assembler import FfmpegMovieAssembler
from media_movie.request_reader import read_movie_request
from media_movie.receipts import inspect_movie_receipt
from media_image.contract import validate_operation_id
from media_movie.service import MovieService
from media_speech.contract import SpeechError
from media_video.contract import VideoError
from media_video.files import read_json


def build_parser():
    state_root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    parser = argparse.ArgumentParser(
        description="Generate scene assets through the public media APIs and assemble a verified narrated MP4."
    )
    parser.add_argument(
        "--state-directory", type=Path, default=state_root / "media-movie"
    )
    parser.add_argument(
        "--image-state-directory", type=Path, default=state_root / "media-image"
    )
    parser.add_argument(
        "--speech-state-directory", type=Path, default=state_root / "media-speech"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "providers",
        help="Discover assembly formats, scene controls and supported image/narration providers.",
    )
    commands.add_parser(
        "example",
        help="Print a scene request; choose a voice from media-speech voices before generating.",
    )
    commands.add_parser("schema", help="Print the JSON Schema for movie requests.")
    generate = commands.add_parser(
        "generate",
        help="Generate real scene assets and return a verified MP4 or replay a successful job.",
    )
    generate.add_argument("--request-file", required=True, type=Path)
    inspect = commands.add_parser(
        "inspect",
        help="Verify retained scene inputs, movie and thumbnail without dispatching any provider.",
    )
    inspect.add_argument("operation_id")
    return parser


def execute_movie_command(args):
    if args.command == "providers":
        result = describe_movie_providers()
    elif args.command == "example":
        result = example_movie_request()
    elif args.command == "schema":
        result = json.loads(
            (Path(__file__).parent / "media_movie/request.schema.json").read_bytes()
        )
    elif args.command == "inspect":
        validate_operation_id(args.operation_id)
        result = inspect_movie_receipt(
            args.state_directory.expanduser().absolute() / args.operation_id,
            args.operation_id,
        )
    else:
        state_directory = args.state_directory.expanduser().absolute()
        assembler = FfmpegMovieAssembler(
            os.environ["MEDIA_MOVIE_FFMPEG"], os.environ["MEDIA_MOVIE_FFPROBE"]
        )
        assets = MovieAssetGateway(
            os.environ["MEDIA_IMAGE_COMMAND"],
            os.environ["MEDIA_SPEECH_COMMAND"],
            args.image_state_directory.expanduser().absolute(),
            args.speech_state_directory.expanduser().absolute(),
        )
        service = MovieService(state_directory, assets, assembler)
        document = read_json(args.request_file.expanduser().absolute())
        request = read_movie_request(document)
        operation_id = document.get("operation_id") or str(uuid.uuid4())
        print(json.dumps({"operation_id": operation_id}), file=sys.stderr, flush=True)
        result = service.generate(operation_id, request)
    return result


def main(arguments=None):
    args = build_parser().parse_args(arguments)
    try:
        result = execute_movie_command(args)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
        return 0
    except (ImageError, MovieError, SpeechError, VideoError) as error:
        print(json.dumps({"error": error.category}), file=sys.stderr)
        return 1
    except KeyError:
        print(json.dumps({"error": "movie_runtime_unavailable"}), file=sys.stderr)
        return 1
    except (OSError, UnicodeError, ValueError):
        print(json.dumps({"error": "storage_failed"}), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
