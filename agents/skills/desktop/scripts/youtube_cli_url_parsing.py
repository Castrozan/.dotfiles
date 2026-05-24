import re

VIDEO_ID_URL_PATTERNS = [
    r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
    r"^([a-zA-Z0-9_-]{11})$",
]
PLAYLIST_ID_URL_PATTERN = r"[?&]list=([a-zA-Z0-9_-]+)"


def extract_video_id_from_url(url):
    for pattern in VIDEO_ID_URL_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url


def extract_playlist_id_from_url(url):
    match = re.search(PLAYLIST_ID_URL_PATTERN, url)
    return match.group(1) if match else url
