import importlib
import sys
from pathlib import Path


PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "stremio_gateway"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))

managed_profile = importlib.import_module("managed_profile")


def test_managed_profile_script_precedes_the_upstream_application():
    index_html = b'<body><script src="release/scripts/main.js"></script></body>'

    injected_html = managed_profile.inject_managed_profile_script(index_html)

    assert injected_html.index(b"/managed-profile.js") < injected_html.index(
        b"release/scripts/main.js"
    )
    assert managed_profile.inject_managed_profile_script(injected_html) == injected_html


def test_managed_profile_script_receives_the_selected_streaming_server():
    script = managed_profile.render_managed_profile_script(
        "https://stream.example.com/server/"
    ).decode()

    assert '"https://stream.example.com/server/"' in script
    assert managed_profile.STREAMING_SERVER_URL_PLACEHOLDER not in script
    assert managed_profile.CONFIGURATION_PLACEHOLDER not in script
    assert "com.lucaszanoni.prowlarr-streams" not in script
    assert "stremio.comet.fast" in script
    assert "https://v3-cinemeta.strem.io/manifest.json" in script
    assert '"schemaVersion":"25"' in script
    assert "addonsLocked: true" in script


def test_managed_profile_uses_the_request_origin_streaming_server():
    assert (
        managed_profile.select_streaming_server_url(
            "stream.example.com",
            "stream.example.com",
            "http://100.64.0.1:11470/",
            "https://stream.example.com/server/",
        )
        == "https://stream.example.com/server/"
    )
    assert (
        managed_profile.select_streaming_server_url(
            "100.64.0.1:43212",
            "stream.example.com",
            "http://100.64.0.1:11470/",
            "https://stream.example.com/server/",
        )
        == "http://100.64.0.1:11470/"
    )
