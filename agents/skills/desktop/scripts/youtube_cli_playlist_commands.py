import json

from youtube_cli_authentication import get_authenticated_service
from youtube_cli_url_parsing import extract_video_id_from_url


def list_playlist(playlist_id, max_results=50):
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
            results.append(
                {"status": "error", "video_id": video_id, "error": str(exception)}
            )

    print(json.dumps(results, indent=2))


def remove_from_playlist(playlist_item_ids):
    youtube = get_authenticated_service()
    results = []

    for item_id in playlist_item_ids:
        try:
            youtube.playlistItems().delete(id=item_id.strip()).execute()
            results.append({"status": "removed", "playlist_item_id": item_id})
        except Exception as exception:
            results.append(
                {
                    "status": "error",
                    "playlist_item_id": item_id,
                    "error": str(exception),
                }
            )

    print(json.dumps(results, indent=2))


def list_my_playlists(max_results=25):
    youtube = get_authenticated_service()
    request = youtube.playlists().list(
        part="snippet,contentDetails", mine=True, maxResults=max_results
    )
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
