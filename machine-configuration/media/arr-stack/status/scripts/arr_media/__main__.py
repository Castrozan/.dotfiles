import argparse
import json
import os
import sys
import urllib.error
from pathlib import Path

from jellyseerr_media import public_requester, public_status


def positive_integer(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def argument_parser():
    parser = argparse.ArgumentParser(
        description="Search and request public movies or TV through Jellyseerr."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    search = commands.add_parser("search")
    search.add_argument("title")
    for command in ("status", "request"):
        action = commands.add_parser(command)
        action.add_argument("media_type", choices=("movie", "tv"))
        action.add_argument(
            "media_id", type=positive_integer, help="TMDB ID from search"
        )
        if command == "request":
            seasons = action.add_mutually_exclusive_group()
            seasons.add_argument("--seasons", nargs="+", type=positive_integer)
            seasons.add_argument("--all-seasons", action="store_true")
    return parser


def request_media(client, arguments, details):
    status = public_status(client, details, arguments.media_type)
    payload = {"mediaType": arguments.media_type, "mediaId": arguments.media_id}
    if arguments.media_type == "tv":
        selected_seasons = (
            status["seasons"]
            if arguments.all_seasons
            else sorted(set(arguments.seasons))
        )
        if not selected_seasons or not set(selected_seasons) <= set(status["seasons"]):
            raise ValueError("Select existing nonempty seasons from status")
        requested_seasons = {
            season["seasonNumber"]
            for request in client.public_requests(details)
            if request["status"] in {1, 2, 5}
            for season in request.get("seasons", [])
            if season.get("status") in {1, 2, 5}
        }
        remaining_seasons = sorted(set(selected_seasons) - requested_seasons)
        if not remaining_seasons:
            return {"result": "already_requested", **status}
        payload["seasons"] = remaining_seasons
    elif any(
        request["status"] in {"pending", "approved", "completed"}
        for request in status["requests"]
    ):
        return {"result": "already_requested", **status}
    request = client.request("POST", "/request", payload)
    return {
        "result": "requested",
        "request_id": request["id"],
        "status": {1: "pending", 2: "approved"}.get(request["status"], "unknown"),
        "media_type": arguments.media_type,
        "media_id": arguments.media_id,
        "seasons": payload.get("seasons", []),
    }


def main(argv=None):
    parser = argument_parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "request":
        has_seasons = bool(arguments.seasons or arguments.all_seasons)
        if has_seasons != (arguments.media_type == "tv"):
            parser.error(
                "TV requests require --seasons or --all-seasons; movies take neither"
            )
    try:
        client = public_requester(
            os.environ.get("ARR_MEDIA_STACK_HOME", Path.home() / "arr-stack")
        )
        if arguments.command == "search":
            result = {"results": client.search(arguments.title)}
        else:
            details = client.details(arguments.media_type, arguments.media_id)
            result = (
                request_media(client, arguments, details)
                if arguments.command == "request"
                else public_status(client, details, arguments.media_type)
            )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except urllib.error.HTTPError as error:
        print(
            f"Jellyseerr request failed (HTTP {error.code}); no success confirmed",
            file=sys.stderr,
        )
    except (OSError, ValueError, KeyError):
        print(
            "Media command failed; check the public requester and Jellyseerr service",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
