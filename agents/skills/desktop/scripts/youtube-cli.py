#!/usr/bin/env python3
"""YouTube CLI: search videos and manage playlists via YouTube Data API v3."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from youtube_cli_authentication import (  # noqa: E402, F401
    CREDENTIALS_PATH,
    SCOPES,
    TOKEN_PATH,
    get_authenticated_service,
)
from youtube_cli_playlist_commands import (  # noqa: E402, F401
    add_to_playlist,
    create_playlist,
    list_my_playlists,
    list_playlist,
    remove_from_playlist,
)
from youtube_cli_search_commands import (  # noqa: E402, F401
    search_videos,
    video_info,
)
from youtube_cli_url_parsing import (  # noqa: E402, F401
    extract_playlist_id_from_url,
    extract_video_id_from_url,
)


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="YouTube CLI: search and manage playlists"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search YouTube videos")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-n", "--max-results", type=int, default=10, help="Number of results"
    )

    playlist_list_parser = subparsers.add_parser(
        "playlist-list", help="List videos in a playlist"
    )
    playlist_list_parser.add_argument("playlist", help="Playlist ID or URL")
    playlist_list_parser.add_argument("-n", "--max-results", type=int, default=50)

    playlist_add_parser = subparsers.add_parser(
        "playlist-add", help="Add videos to a playlist"
    )
    playlist_add_parser.add_argument("playlist", help="Playlist ID or URL")
    playlist_add_parser.add_argument("videos", nargs="+", help="Video IDs or URLs")

    playlist_remove_parser = subparsers.add_parser(
        "playlist-remove", help="Remove videos from playlist"
    )
    playlist_remove_parser.add_argument(
        "item_ids", nargs="+", help="Playlist item IDs (from playlist-list)"
    )

    subparsers.add_parser("playlists", help="List your playlists")

    create_parser = subparsers.add_parser(
        "playlist-create", help="Create a new playlist"
    )
    create_parser.add_argument("title", help="Playlist title")
    create_parser.add_argument("-d", "--description", default="")
    create_parser.add_argument(
        "-p", "--privacy", choices=["public", "private", "unlisted"], default="private"
    )

    info_parser = subparsers.add_parser("info", help="Get video details")
    info_parser.add_argument("videos", nargs="+", help="Video IDs or URLs")

    return parser


def dispatch_command(args):
    if args.command == "search":
        search_videos(args.query, args.max_results)
    elif args.command == "playlist-list":
        list_playlist(extract_playlist_id_from_url(args.playlist), args.max_results)
    elif args.command == "playlist-add":
        add_to_playlist(extract_playlist_id_from_url(args.playlist), args.videos)
    elif args.command == "playlist-remove":
        remove_from_playlist(args.item_ids)
    elif args.command == "playlists":
        list_my_playlists()
    elif args.command == "playlist-create":
        create_playlist(args.title, args.description, args.privacy)
    elif args.command == "info":
        video_ids = [extract_video_id_from_url(v) for v in args.videos]
        video_info(video_ids)


def main():
    parser = build_argument_parser()
    args = parser.parse_args()
    dispatch_command(args)


if __name__ == "__main__":
    main()
