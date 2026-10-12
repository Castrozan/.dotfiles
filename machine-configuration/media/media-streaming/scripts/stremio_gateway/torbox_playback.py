import urllib.error
import urllib.parse
import urllib.request

from comet_stream_adapter import CometResponse


MEDIA_CHUNK_BYTES = 256 * 1024
MEDIA_REQUEST_TIMEOUT_SECONDS = 30
MEDIA_RESPONSE_HEADERS = (
    "Content-Type",
    "Content-Length",
    "Content-Range",
    "Accept-Ranges",
)


class HttpsMediaRequest(urllib.request.Request):
    def __init__(self, location: str, headers: dict[str, str], method: str):
        if urllib.parse.urlsplit(location).scheme != "https":
            raise ValueError("media location must use https")
        super().__init__(location, headers=headers, method=method)


def relay_torbox_playback(handler, response: CometResponse, include_body: bool) -> bool:
    if response.status != 302 or response.location is None:
        return False
    upstream = _open_upstream(handler, response.location, include_body)
    with upstream:
        _send_media_headers(handler, upstream)
        if include_body:
            _relay_media_body(handler, upstream)
    return True


def _open_upstream(handler, location: str, include_body: bool):
    headers = {"User-Agent": "Comet"}
    if handler.headers.get("Range") is not None:
        headers["Range"] = handler.headers["Range"]
    try:
        request = HttpsMediaRequest(
            location, headers, "GET" if include_body else "HEAD"
        )
        return urllib.request.build_opener().open(
            request, timeout=MEDIA_REQUEST_TIMEOUT_SECONDS
        )
    except Exception:
        raise RuntimeError("TorBox media request failed") from None


def _send_media_headers(handler, upstream) -> None:
    handler.send_response(upstream.status)
    handler._send_cors_headers()
    for name in MEDIA_RESPONSE_HEADERS:
        if upstream.headers.get(name) is not None:
            handler.send_header(name, upstream.headers[name])
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()


def _relay_media_body(handler, upstream) -> None:
    try:
        while chunk := upstream.read(MEDIA_CHUNK_BYTES):
            handler.wfile.write(chunk)
    except (BrokenPipeError, ConnectionResetError, TimeoutError):
        handler.close_connection = True
