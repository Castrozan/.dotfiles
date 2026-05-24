import json
import subprocess
import sys

from youtube_cli_authentication import get_authenticated_service


def search_videos(query, max_results=10):
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
        print(
            json.dumps({"error": "search_failed", "stderr": result.stderr}),
            file=sys.stderr,
        )
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
                "url": data.get("url")
                or f"https://www.youtube.com/watch?v={data.get('id')}",
                "channel": data.get("channel") or data.get("uploader"),
                "duration": data.get("duration"),
                "view_count": data.get("view_count"),
                "description": (data.get("description") or "")[:200],
            }
        )

    print(json.dumps(videos, indent=2))


def video_info(video_ids):
    youtube = get_authenticated_service()
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics", id=",".join(video_ids)
    )
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
