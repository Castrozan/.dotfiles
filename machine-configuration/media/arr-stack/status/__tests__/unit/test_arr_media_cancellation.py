import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

PACKAGE_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts/arr_media"
sys.path.insert(0, str(PACKAGE_DIRECTORY))
specification = importlib.util.spec_from_file_location(
    "arr_media_cancellation_cli", PACKAGE_DIRECTORY / "__main__.py"
)
cli = importlib.util.module_from_spec(specification)
specification.loader.exec_module(cli)
JellyseerrMedia = importlib.import_module("jellyseerr_media").JellyseerrMedia


@pytest.fixture
def client(monkeypatch):
    client = JellyseerrMedia("secret", 2)
    monkeypatch.setattr(cli, "public_requester", lambda _: client)
    return client


@pytest.mark.parametrize("requester_id,is_4k", [(2, False), (3, False), (2, True)])
@pytest.mark.parametrize("media_type", ["movie", "tv"])
def test_cancellation_removes_only_the_selected_public_request(
    client, monkeypatch, capsys, requester_id, is_4k, media_type
):
    details = {
        "id": 769,
        "mediaInfo": {
            "requests": [
                {
                    "id": 65,
                    "requestedBy": {"id": requester_id},
                    "is4k": is_4k,
                    "status": 2,
                },
                {"id": 66, "requestedBy": {"id": 2}, "status": 2},
            ]
        },
    }
    monkeypatch.setattr(type(client), "details", lambda *_: details)
    transport = Mock()
    monkeypatch.setattr(type(client), "request", transport)

    assert cli.main(["cancel", media_type, "769", "65"]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["downloads"] == "unchanged"
    if requester_id == 2 and not is_4k:
        transport.assert_called_once_with("DELETE", "/request/65")
        assert result["result"] == "request_removed"
    else:
        transport.assert_not_called()
        assert result["result"] == "not_requested"


def test_repeated_cancellation_does_not_delete_anything(client, monkeypatch, capsys):
    monkeypatch.setattr(
        type(client), "details", lambda *_: {"id": 769, "mediaInfo": {"requests": []}}
    )
    transport = Mock()
    monkeypatch.setattr(type(client), "request", transport)

    assert cli.main(["cancel", "movie", "769", "65"]) == 0

    transport.assert_not_called()
    assert json.loads(capsys.readouterr().out)["result"] == "not_requested"


def test_cancellation_http_failure_never_claims_removal(client, monkeypatch, capsys):
    monkeypatch.setattr(
        type(client),
        "details",
        lambda *_: {
            "id": 769,
            "mediaInfo": {"requests": [{"id": 65, "requestedBy": {"id": 2}}]},
        },
    )
    monkeypatch.setattr(
        type(client), "request", Mock(side_effect=cli.JellyseerrRequestError(403))
    )

    assert cli.main(["cancel", "movie", "769", "65"]) == 1

    captured = capsys.readouterr()
    assert not captured.out
    assert "cancel failed (HTTP 403)" in captured.err


def test_delete_accepts_jellyseerr_empty_success_response(client, monkeypatch):
    connection = Mock()
    connection.getresponse.return_value.status = 204
    connection.getresponse.return_value.read.return_value = b""
    monkeypatch.setattr(
        cli.http.client, "HTTPConnection", lambda *_args, **_kwargs: connection
    )

    assert client.request("DELETE", "/request/65") is None

    connection.close.assert_called_once()
