import importlib.util
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import Mock

import pytest

PACKAGE_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts/arr_media"
sys.path.insert(0, str(PACKAGE_DIRECTORY))
specification = importlib.util.spec_from_file_location(
    "arr_media_cli", PACKAGE_DIRECTORY / "__main__.py"
)
cli = importlib.util.module_from_spec(specification)
specification.loader.exec_module(cli)
JellyseerrMedia = importlib.import_module("jellyseerr_media").JellyseerrMedia


@pytest.fixture
def client(monkeypatch):
    client = JellyseerrMedia("secret", 2)
    monkeypatch.setattr(cli, "public_requester", lambda _: client)
    return client


@pytest.fixture
def details():
    return {
        "id": 4574,
        "name": "X-Men",
        "seasons": [
            {"seasonNumber": number, "episodeCount": 13} for number in range(6)
        ],
        "mediaInfo": {"requests": []},
    }


@pytest.mark.parametrize(
    "arguments",
    [
        ["request", "tv", "4574"],
        ["request", "movie", "36657", "--seasons", "1"],
        ["request", "tv", "4574", "--seasons", "0"],
        ["status", "movie", "-1"],
        ["request", "movie", "36657; reboot"],
    ],
)
def test_invalid_request_never_accesses_credentials(monkeypatch, arguments):
    credentials = Mock()
    monkeypatch.setattr(cli, "public_requester", credentials)
    with pytest.raises(SystemExit) as error:
        cli.main(arguments)
    assert error.value.code == 2
    credentials.assert_not_called()


def test_tv_request_preserves_explicit_seasons(client, details, monkeypatch, capsys):
    transport = Mock(return_value={"id": 8, "status": 2})
    monkeypatch.setattr(JellyseerrMedia, "request", transport)
    monkeypatch.setattr(JellyseerrMedia, "details", lambda *_: details)
    assert (
        cli.main(["request", "tv", "4574", "--seasons", "1", "2", "3", "4", "5"]) == 0
    )
    transport.assert_called_once_with(
        "POST",
        "/request",
        {"mediaType": "tv", "mediaId": 4574, "seasons": [1, 2, 3, 4, 5]},
    )
    result = json.loads(capsys.readouterr().out)
    assert result["result"] == "requested"
    assert result["status"] == "approved"
    assert "downloading" not in str(result)


def test_all_seasons_excludes_specials_and_existing_requests(
    client, details, monkeypatch
):
    details["mediaInfo"]["requests"] = [
        {
            "id": 7,
            "status": 2,
            "requestedBy": {"id": 2},
            "seasons": [{"seasonNumber": 1, "status": 2}],
        }
    ]
    transport = Mock(return_value={"id": 8, "status": 2})
    monkeypatch.setattr(JellyseerrMedia, "request", transport)
    arguments = cli.argument_parser().parse_args(
        ["request", "tv", "4574", "--all-seasons"]
    )
    cli.request_media(client, arguments, details)
    assert transport.call_args.args[2]["seasons"] == [2, 3, 4, 5]


def test_invalid_season_never_posts(client, details, monkeypatch):
    transport = Mock()
    monkeypatch.setattr(JellyseerrMedia, "request", transport)
    arguments = cli.argument_parser().parse_args(
        ["request", "tv", "4574", "--seasons", "6"]
    )
    with pytest.raises(ValueError):
        cli.request_media(client, arguments, details)
    transport.assert_not_called()


def test_repeat_movie_request_is_idempotent(client, details, monkeypatch):
    details["mediaInfo"]["requests"] = [
        {"id": 7, "status": 2, "requestedBy": {"id": 2}}
    ]
    transport = Mock()
    monkeypatch.setattr(JellyseerrMedia, "request", transport)
    arguments = cli.argument_parser().parse_args(["request", "movie", "4574"])
    assert (
        cli.request_media(client, arguments, details)["result"] == "already_requested"
    )
    transport.assert_not_called()


def test_movie_request_uses_only_public_defaults(client, details, monkeypatch):
    transport = Mock(return_value={"id": 8, "status": 2})
    monkeypatch.setattr(JellyseerrMedia, "request", transport)
    arguments = cli.argument_parser().parse_args(["request", "movie", "4574"])
    cli.request_media(client, arguments, details)
    transport.assert_called_once_with(
        "POST", "/request", {"mediaType": "movie", "mediaId": 4574}
    )


@pytest.mark.parametrize(
    "failure",
    [
        urllib.error.HTTPError(
            "http://secret", 409, "private title and secret", {}, None
        ),
        urllib.error.URLError("secret"),
        ValueError("secret"),
    ],
)
def test_errors_never_claim_success_or_reveal_details(
    client, monkeypatch, capsys, failure
):
    monkeypatch.setattr(JellyseerrMedia, "search", Mock(side_effect=failure))
    assert cli.main(["search", "Blade"]) == 1
    captured = capsys.readouterr()
    assert not captured.out
    assert "secret" not in captured.err
    assert "private title" not in captured.err
