import argparse
import http.client
import json
import os
import sys
from pathlib import Path

from jellyseerr_media import JellyseerrRequestError, public_requester, public_status
from media_removal import MediaRemovalDenied, authorize_media_removal, remove_media


def positive_integer(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def argument_parser():
    parser = argparse.ArgumentParser(
        description="Search public movies and TV, request titles or withdraw requests."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    search = commands.add_parser("search")
    search.add_argument("title")
    descriptions = {
        "cancel": "Remove one public request record; downloads and library files stay unchanged.",
        "remove": "Operator only: remove one public library title and its files.",
    }
    for command in ("status", "request", "cancel", "remove"):
        action = commands.add_parser(
            command,
            description=descriptions.get(command),
        )
        action.add_argument("media_type", choices=("movie", "tv"))
        action.add_argument(
            "media_id", type=positive_integer, help="TMDB ID from search"
        )
        if command == "cancel":
            action.add_argument(
                "request_id",
                type=positive_integer,
                help="Public request ID from status",
            )
        if command == "request":
            seasons = action.add_mutually_exclusive_group()
            seasons.add_argument("--seasons", nargs="+", type=positive_integer)
            seasons.add_argument("--all-seasons", action="store_true")
    return parser


def selected_tv_seasons(arguments, status):
    selected = (
        status["seasons"] if arguments.all_seasons else sorted(set(arguments.seasons))
    )
    if not selected or not set(selected) <= set(status["seasons"]):
        raise ValueError("Select existing nonempty seasons from status")
    return selected


def active_request_seasons(requests):
    return {
        season["seasonNumber"]
        for request in requests
        if request["status"] in {1, 2, 5}
        for season in request.get("seasons", [])
        if season.get("status") in {1, 2, 5}
    }


def movie_is_requested(status):
    return any(
        request["status"] in {"pending", "approved", "completed"}
        for request in status["requests"]
    )


def request_media(client, arguments, details):
    status = public_status(client, details, arguments.media_type)
    payload = {"mediaType": arguments.media_type, "mediaId": arguments.media_id}
    if arguments.media_type == "tv":
        selected = selected_tv_seasons(arguments, status)
        requested = active_request_seasons(client.public_requests(details))
        remaining_seasons = sorted(set(selected) - requested)
        if not remaining_seasons:
            return {"result": "already_requested", **status}
        payload["seasons"] = remaining_seasons
    elif movie_is_requested(status):
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


def validate_request_arguments(parser, arguments):
    if arguments.command != "request":
        return
    has_seasons = bool(arguments.seasons or arguments.all_seasons)
    if has_seasons != (arguments.media_type == "tv"):
        parser.error(
            "TV requests require --seasons or --all-seasons; movies take neither"
        )


def cancel_media_request(client, arguments, details):
    requested = any(
        request["id"] == arguments.request_id
        for request in client.public_requests(details)
    )
    if requested:
        client.request("DELETE", f"/request/{arguments.request_id}")
    return {
        "result": "request_removed" if requested else "not_requested",
        "media_type": arguments.media_type,
        "media_id": arguments.media_id,
        "request_id": arguments.request_id,
        "downloads": "unchanged",
    }


def execute_command(client, arguments):
    if arguments.command == "search":
        return {"results": client.search(arguments.title)}
    if arguments.command == "remove":
        return remove_media(
            client,
            os.environ.get("ARR_MEDIA_STACK_HOME", Path.home() / "arr-stack"),
            arguments.media_type,
            arguments.media_id,
        )
    details = client.details(arguments.media_type, arguments.media_id)
    if arguments.command == "request":
        return request_media(client, arguments, details)
    if arguments.command == "cancel":
        return cancel_media_request(client, arguments, details)
    return public_status(client, details, arguments.media_type)


def client_for_command(arguments):
    if arguments.command == "remove":
        authorize_media_removal()
    return public_requester(
        os.environ.get("ARR_MEDIA_STACK_HOME", Path.home() / "arr-stack")
    )


def main(argv=None):
    parser = argument_parser()
    arguments = parser.parse_args(argv)
    validate_request_arguments(parser, arguments)
    try:
        client = client_for_command(arguments)
        result = execute_command(client, arguments)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except MediaRemovalDenied as error:
        print(str(error), file=sys.stderr)
    except JellyseerrRequestError as error:
        print(
            f"Jellyseerr {arguments.command} failed (HTTP {error.status}); no success confirmed",
            file=sys.stderr,
        )
    except (OSError, ValueError, KeyError, http.client.HTTPException):
        print(
            "Media removal failed or is unconfirmed; no success confirmed"
            if arguments.command == "remove"
            else "Media command failed; check the public requester and Jellyseerr service",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
