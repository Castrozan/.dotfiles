import http.client
import http.server
import threading

import pytest

import serve


@pytest.fixture
def renderer_server(tmp_path):
    (tmp_path / "renderer.js").write_text("current")
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), serve.renderer_handler(str(tmp_path))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_address[1]
    server.shutdown()


def fetch(port, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request("GET", "/renderer.js", headers=headers or {})
    response = connection.getresponse()
    body = response.read()
    connection.close()
    return response, body


def test_the_browser_is_told_never_to_keep_a_copy(renderer_server):
    response, _ = fetch(renderer_server)
    assert response.getheader("Cache-Control") == "no-store"


def test_a_stale_copy_is_replaced_despite_identical_store_timestamps(renderer_server):
    response, body = fetch(
        renderer_server, {"If-Modified-Since": "Thu, 01 Jan 2099 00:00:00 GMT"}
    )
    assert response.status == 200
    assert body == b"current"
