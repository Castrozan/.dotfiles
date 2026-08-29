import json
from pathlib import Path


MANAGED_PROFILE_SCRIPT_TAG = b'<script src="/managed-profile.js"></script>'
STREAMING_SERVER_URL_PLACEHOLDER = "__STREMIO_MANAGED_STREAMING_SERVER_URL__"
MANAGED_PROFILE_SCRIPT_TEMPLATE = (
    Path(__file__).with_suffix(".js").read_text(encoding="utf-8")
)


def inject_managed_profile_script(index_html: bytes) -> bytes:
    if MANAGED_PROFILE_SCRIPT_TAG in index_html:
        return index_html
    insertion_offset = index_html.find(b"<script src=")
    if insertion_offset < 0:
        raise RuntimeError("Stremio index has no application script")
    return (
        index_html[:insertion_offset]
        + MANAGED_PROFILE_SCRIPT_TAG
        + index_html[insertion_offset:]
    )


def render_managed_profile_script(streaming_server_url: str) -> bytes:
    if STREAMING_SERVER_URL_PLACEHOLDER not in MANAGED_PROFILE_SCRIPT_TEMPLATE:
        raise RuntimeError("managed profile script has no streaming server placeholder")
    return MANAGED_PROFILE_SCRIPT_TEMPLATE.replace(
        STREAMING_SERVER_URL_PLACEHOLDER,
        json.dumps(streaming_server_url),
    ).encode()


def select_streaming_server_url(
    request_host: str,
    public_host: str,
    tailnet_streaming_server_url: str,
    public_streaming_server_url: str,
) -> str:
    return (
        public_streaming_server_url
        if request_host == public_host
        else tailnet_streaming_server_url
    )
