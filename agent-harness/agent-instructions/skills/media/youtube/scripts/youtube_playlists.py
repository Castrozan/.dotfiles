import json

from youtube_authentication import get_authenticated_service


def list_my_playlists(max_results=25):
    """List the authenticated user's playlists."""
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
