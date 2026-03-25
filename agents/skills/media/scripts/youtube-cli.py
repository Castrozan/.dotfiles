#!/usr/bin/env python3
"""YouTube CLI — search videos and manage playlists via YouTube Data API v3."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CREDENTIALS_PATH = os.environ.get(
    "YOUTUBE_CLI_CREDENTIALS", str(Path.home() / ".config" / "youtube-cli" / "credentials.json")
)
TOKEN_PATH = os.environ.get(
    "YOUTUBE_CLI_TOKEN", str(Path.home() / ".config" / "youtube-cli" / "token.json")
)
SCOPES = ["https://www.googleapis.com/auth/youtube"]


def get_authenticated_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    credentials = None
    token_path = Path(TOKEN_PATH)

    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            credentials_path = Path(CREDENTIALS_PATH)
            if not credentials_path.exists():
                print(
                    json.dumps(
                        {
                            "error": "missing_credentials",
                            "message": f"OAuth credentials not found at {CREDENTIALS_PATH}. "
                            "Download client_secret.json from Google Cloud Console "
                            "(APIs & Services > Credentials > OAuth 2.0 Client IDs) "
                            "and save it there.",
                        }
                    ),
                    file=sys.stderr,
                )
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            credentials = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json())

    return build("youtube", "v3", credentials=credentials)


def search_videos(query, max_results=10):
    """Search YouTube using yt-dlp (no auth needed)."""
    search_query = f"ytsearch{max_results}:{query}"
    result = subprocess.run(
        [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--no-warnings",
            search_query,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(json.dumps({"error": "search_failed", "stderr": result.stderr}), file=sys.stderr)
        sys.exit(1)

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        data = json.loads(line)
        videos.append(
            {
                "id": data.get("id"),
                "title": data.get("title"),
                "url": data.get("url") or f"https://www.youtube.com/watch?v={data.get('id')}",
                "channel": data.get("channel") or data.get("uploader"),
                "duration": data.get("duration"),
                "view_count": data.get("view_count"),
                "description": (data.get("description") or "")[:200],
            }
        )

    print(json.dumps(videos, indent=2))


def list_playlist(playlist_id, max_results=50):
    """List videos in a playlist."""
    youtube = get_authenticated_service()
    videos = []
    next_page_token = None

    while len(videos) < max_results:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=min(50, max_results - len(videos)),
            pageToken=next_page_token,
        )
        response = request.execute()

        for item in response.get("items", []):
            snippet = item["snippet"]
            videos.append(
                {
                    "id": item["id"],
                    "video_id": snippet["resourceId"]["videoId"],
                    "title": snippet["title"],
                    "channel": snippet.get("videoOwnerChannelTitle", ""),
                    "position": snippet["position"],
                    "url": f"https://www.youtube.com/watch?v={snippet['resourceId']['videoId']}",
                }
            )

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    print(json.dumps(videos, indent=2))


def add_to_playlist(playlist_id, video_ids):
    """Add one or more videos to a playlist."""
    youtube = get_authenticated_service()
    results = []

    for video_id in video_ids:
        video_id = video_id.strip()
        if "youtube.com" in video_id or "youtu.be" in video_id:
            video_id = extract_video_id_from_url(video_id)

        try:
            request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            )
            response = request.execute()
            results.append(
                {
                    "status": "added",
                    "video_id": video_id,
                    "title": response["snippet"]["title"],
                    "position": response["snippet"]["position"],
                }
            )
        except Exception as exception:
            results.append({"status": "error", "video_id": video_id, "error": str(exception)})

    print(json.dumps(results, indent=2))


def remove_from_playlist(playlist_item_ids):
    """Remove videos from a playlist by playlist item ID."""
    youtube = get_authenticated_service()
    results = []

    for item_id in playlist_item_ids:
        try:
            youtube.playlistItems().delete(id=item_id.strip()).execute()
            results.append({"status": "removed", "playlist_item_id": item_id})
        except Exception as exception:
            results.append({"status": "error", "playlist_item_id": item_id, "error": str(exception)})

    print(json.dumps(results, indent=2))


def list_my_playlists(max_results=25):
    """List the authenticated user's playlists."""
    youtube = get_authenticated_service()
    request = youtube.playlists().list(part="snippet,contentDetails", mine=True, maxResults=max_results)
    response = request.execute()

    playlists = []
    for item in response.get("items", []):
        playlists.append(
            {
                "id": item["id"],
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", ""),
                "video_count": item["contentDetails"]["itemCount"],
                "url": f"https://www.youtube.com/playlist?list={item['id']}",
            }
        )

    print(json.dumps(playlists, indent=2))


def create_playlist(title, description="", privacy="private"):
    """Create a new playlist."""
    youtube = get_authenticated_service()
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": description},
            "status": {"privacyStatus": privacy},
        },
    )
    response = request.execute()

    print(
        json.dumps(
            {
                "id": response["id"],
                "title": response["snippet"]["title"],
                "url": f"https://www.youtube.com/playlist?list={response['id']}",
                "privacy": response["status"]["privacyStatus"],
            },
            indent=2,
        )
    )


def video_info(video_ids):
    """Get detailed info about specific videos."""
    youtube = get_authenticated_service()
    request = youtube.videos().list(part="snippet,contentDetails,statistics", id=",".join(video_ids))
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        videos.append(
            {
                "id": item["id"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "description": item["snippet"].get("description", "")[:300],
                "duration": item["contentDetails"]["duration"],
                "view_count": item["statistics"].get("viewCount"),
                "like_count": item["statistics"].get("likeCount"),
                "url": f"https://www.youtube.com/watch?v={item['id']}",
            }
        )

    print(json.dumps(videos, indent=2))


def extract_video_id_from_url(url):
    """Extract video ID from various YouTube URL formats."""
    import re

    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url


def extract_playlist_id_from_url(url):
    """Extract playlist ID from YouTube URL or return as-is."""
    import re

    match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else url


def main():
    parser = argparse.ArgumentParser(description="YouTube CLI — search and manage playlists")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search YouTube videos")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-n", "--max-results", type=int, default=10, help="Number of results")

    playlist_list_parser = subparsers.add_parser("playlist-list", help="List videos in a playlist")
    playlist_list_parser.add_argument("playlist", help="Playlist ID or URL")
    playlist_list_parser.add_argument("-n", "--max-results", type=int, default=50)

    playlist_add_parser = subparsers.add_parser("playlist-add", help="Add videos to a playlist")
    playlist_add_parser.add_argument("playlist", help="Playlist ID or URL")
    playlist_add_parser.add_argument("videos", nargs="+", help="Video IDs or URLs")

    playlist_remove_parser = subparsers.add_parser("playlist-remove", help="Remove videos from playlist")
    playlist_remove_parser.add_argument("item_ids", nargs="+", help="Playlist item IDs (from playlist-list)")

    subparsers.add_parser("playlists", help="List your playlists")

    create_parser = subparsers.add_parser("playlist-create", help="Create a new playlist")
    create_parser.add_argument("title", help="Playlist title")
    create_parser.add_argument("-d", "--description", default="")
    create_parser.add_argument("-p", "--privacy", choices=["public", "private", "unlisted"], default="private")

    info_parser = subparsers.add_parser("info", help="Get video details")
    info_parser.add_argument("videos", nargs="+", help="Video IDs or URLs")

    args = parser.parse_args()

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


if __name__ == "__main__":
    main()
