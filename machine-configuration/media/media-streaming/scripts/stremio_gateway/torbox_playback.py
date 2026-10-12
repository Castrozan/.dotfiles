import urllib.error
import urllib.request

from comet_stream_adapter import CometResponse


MEDIA_CHUNK_BYTES = 256 * 1024
MEDIA_RESPONSE_HEADERS = (
    "Content-Type",
    "Content-Length",
    "Content-Range",
    "Accept-Ranges",
)


def relay_torbox_playback(handler, response: CometResponse, include_body: bool) -> bool:
    if response.status != 302 or response.location is None:
        return False
    headers = {"User-Agent": "Comet"}
    if handler.headers.get("Range") is not None:
        headers["Range"] = handler.headers["Range"]
    request = urllib.request.Request(
        response.location,
        headers=headers,
        method="GET" if include_body else "HEAD",
    )
    try:
        upstream = urllib.request.urlopen(request, timeout=30)
    except Exception:
        raise RuntimeError("TorBox media request failed") from None
    with upstream:
        handler.send_response(upstream.status)
        handler._send_cors_headers()
        for name in MEDIA_RESPONSE_HEADERS:
            if upstream.headers.get(name) is not None:
                handler.send_header(name, upstream.headers[name])
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        if not include_body:
            return True
        try:
            while chunk := upstream.read(MEDIA_CHUNK_BYTES):
                handler.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            handler.close_connection = True
    return True
