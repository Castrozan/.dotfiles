import importlib
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/arr_media"))
media = importlib.import_module("jellyseerr_media")


def test_transport_impersonates_ordinary_requester_with_bounded_timeout(monkeypatch):
    connection = Mock()
    connection.getresponse.return_value.status = 201
    connection.getresponse.return_value.read.return_value = b'{"id":8,"status":2}'
    factory = Mock(return_value=connection)
    monkeypatch.setattr(media.http.client, "HTTPConnection", factory)
    client = media.JellyseerrMedia("secret", 2)
    client.request("POST", "/request", {"mediaType": "movie", "mediaId": 36657})
    factory.assert_called_once_with("127.0.0.1", 5055, timeout=20)
    assert connection.request.call_args.args == ("POST", "/api/v1/request")
    headers = connection.request.call_args.kwargs["headers"]
    assert headers["X-API-User"] == "2"
    assert headers["X-Api-Key"] == "secret"
    assert json.loads(connection.request.call_args.kwargs["body"]) == {
        "mediaType": "movie",
        "mediaId": 36657,
    }
    connection.close.assert_called_once()


def test_http_failure_closes_connection_without_exposing_body(monkeypatch):
    connection = Mock()
    connection.getresponse.return_value.status = 403
    factory = Mock(return_value=connection)
    monkeypatch.setattr(media.http.client, "HTTPConnection", factory)
    with pytest.raises(media.JellyseerrRequestError) as error:
        media.JellyseerrMedia("secret", 2).request("POST", "/request", {})
    assert error.value.status == 403
    connection.getresponse.return_value.read.assert_not_called()
    connection.close.assert_called_once()


@pytest.mark.parametrize(
    "users",
    [
        [],
        [{"id": 1, "jellyfinUsername": "lucas", "permissions": 160}],
    ],
)
def test_missing_requester_is_rejected(tmp_path, monkeypatch, users):
    settings = tmp_path / "config/jellyseerr/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"main": {"apiKey": "secret"}}))
    monkeypatch.setattr(media.JellyseerrMedia, "request", lambda *_: {"results": users})
    with pytest.raises(ValueError):
        media.public_requester(tmp_path)


@pytest.mark.parametrize("permissions", [2, 16, 16384, 8352])
def test_requester_permissions_are_checked_before_impersonation(
    tmp_path, monkeypatch, permissions
):
    settings = tmp_path / "config/jellyseerr/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"main": {"apiKey": "secret"}}))
    monkeypatch.setattr(
        media.JellyseerrMedia,
        "request",
        lambda *_: {
            "results": [
                {"id": 2, "jellyfinUsername": "lucas", "permissions": permissions}
            ]
        },
    )
    if permissions == 8352:
        assert media.public_requester(tmp_path).requester_id == 2
    else:
        with pytest.raises(ValueError):
            media.public_requester(tmp_path)


def test_search_encodes_input_and_discards_service_and_user_data(monkeypatch):
    paths = []

    def request(client, method, path):
        paths.append(path)
        return {
            "results": [
                {
                    "id": 36657,
                    "mediaType": "movie",
                    "title": "X-Men",
                    "releaseDate": "2000-07-12",
                    "mediaInfo": {"secret": "private"},
                    "requestedBy": {"email": "private"},
                },
                {"id": 1, "mediaType": "person", "name": "Actor"},
            ]
        }

    monkeypatch.setattr(media.JellyseerrMedia, "request", request)
    result = media.JellyseerrMedia("secret", 2).search("X-Men & $(reboot)")
    assert "query=X-Men+%26+%24%28reboot%29" in paths[0]
    assert result == [
        {
            "media_id": 36657,
            "media_type": "movie",
            "title": "X-Men",
            "original_title": None,
            "year": "2000",
        }
    ]


def test_status_hides_private_requests_and_availability():
    details = {
        "id": 1,
        "title": "Catalog title",
        "mediaInfo": {
            "status": 5,
            "requests": [
                {"id": 9, "requestedBy": {"id": 3, "email": "private"}, "status": 2}
            ],
        },
    }
    client = media.JellyseerrMedia("secret", 2)
    result = media.public_status(client, details, "movie")
    assert result["requests"] == []
    assert "availability" not in result
    assert "private" not in json.dumps(result)
    details["mediaInfo"]["requests"].append(
        {"id": 10, "requestedBy": {"id": 2}, "status": 2}
    )
    result = media.public_status(client, details, "movie")
    assert result["requests"] == [
        {"request_id": 10, "status": "approved", "seasons": []}
    ]
    assert result["availability"] == "available"
