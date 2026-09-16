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
