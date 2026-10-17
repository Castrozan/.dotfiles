import importlib
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/arr_media"))
library = importlib.import_module("media_library")


@pytest.fixture
def stack(tmp_path):
    settings = {
        "radarr": [
            {
                "id": 0,
                "isDefault": True,
                "is4k": False,
                "hostname": "arr-radarr",
                "port": 7878,
                "activeDirectory": "/data/media/movies",
            }
        ]
    }
    path = tmp_path / "config/jellyseerr"
    path.mkdir(parents=True)
    (path / "settings.json").write_text(json.dumps(settings))
    path = tmp_path / "config/radarr"
    path.mkdir()
    (path / "config.xml").write_text("<Config><ApiKey>secret</ApiKey></Config>")
    (tmp_path / ".env").write_text("ARR_BIND_ADDR=127.0.0.1\n")
    return tmp_path


def test_library_uses_the_same_public_arr_server_as_native_deletion(stack):
    endpoint = library.load_media_library(stack, "movie", 0)
    assert (endpoint.address, endpoint.port, endpoint.resource) == (
        "127.0.0.1",
        7878,
        "movie",
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"activeDirectory": "/data/media/movies-private"},
        {"hostname": "another-server"},
        {"id": 7},
        {"is4k": True},
        {"useSsl": True},
        {"baseUrl": "/another-service"},
    ],
)
def test_unverified_native_deletion_server_is_rejected(stack, changes):
    path = stack / "config/jellyseerr/settings.json"
    settings = json.loads(path.read_text())
    settings["radarr"][0].update(changes)
    path.write_text(json.dumps(settings))
    with pytest.raises(ValueError, match="public stack library"):
        library.load_media_library(stack, "movie", 0)


@pytest.mark.parametrize("status", [200, 404, 503])
def test_library_lookup_closes_connection_and_distinguishes_missing(
    monkeypatch, status
):
    connection = Mock()
    response = connection.getresponse.return_value
    response.status = status
    response.read.return_value = b'{"id":43}'
    monkeypatch.setattr(
        library.http.client, "HTTPConnection", lambda *_args, **_kwargs: connection
    )
    client = library.MediaLibrary("127.0.0.1", 7878, "secret", "movie")
    if status == 503:
        with pytest.raises(ValueError, match="lookup failed"):
            client.item(43)
    else:
        assert client.item(43) == ({"id": 43} if status == 200 else None)
    connection.close.assert_called_once()
