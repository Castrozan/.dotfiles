import sys

from comet_stream_adapter import CometResponse
from torbox_playback import relay_torbox_playback


def proxy_comet_request(handler, request_target: str, include_body: bool) -> None:
    try:
        forwarded_protocol = handler.headers.get("X-Forwarded-Proto", "http")
        request_origin = f"{forwarded_protocol}://{handler.headers['Host']}"
        response = handler.comet_adapter.response(request_target, request_origin)
        if "/playback/" in request_target and relay_torbox_playback(
            handler, response, include_body
        ):
            return
    except Exception as error:
        print(f"Comet proxy failed: {error}", file=sys.stderr, flush=True)
        handler.send_error(502)
        return
    _write_comet_response(handler, response, include_body)


def _write_comet_response(handler, response: CometResponse, include_body: bool) -> None:
    handler.send_response(response.status)
    handler._send_cors_headers()
    handler.send_header("Content-Type", response.content_type)
    handler.send_header("Cache-Control", response.cache_control or "no-store")
    if response.location is not None:
        handler.send_header("Location", response.location)
    handler.send_header("Content-Length", str(len(response.body)))
    handler.end_headers()
    if include_body:
        handler.wfile.write(response.body)
