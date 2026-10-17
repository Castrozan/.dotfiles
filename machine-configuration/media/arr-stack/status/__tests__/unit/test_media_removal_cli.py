import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

PACKAGE_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts/arr_media"
sys.path.insert(0, str(PACKAGE_DIRECTORY))
specification = importlib.util.spec_from_file_location(
    "arr_media_removal_cli", PACKAGE_DIRECTORY / "__main__.py"
)
cli = importlib.util.module_from_spec(specification)
specification.loader.exec_module(cli)


def test_guest_is_rejected_before_credentials_or_media_lookup(monkeypatch, capsys):
    monkeypatch.setenv("ARR_MEDIA_OPERATOR_DISCORD_USER_ID", "owner")
    monkeypatch.setenv(
        "CLAWDE_CHANNEL_PROMPT", '{"source":"discord","user_id":"guest"}'
    )
    factory = Mock()
    monkeypatch.setattr(cli, "public_requester", factory)
    assert cli.main(["remove", "movie", "769"]) == 1
    factory.assert_not_called()
    captured = capsys.readouterr()
    assert not captured.out
    assert "verified Discord operator" in captured.err


@pytest.mark.parametrize("identifier", ["0", "-1", "769; rm -rf /"])
def test_removal_rejects_invalid_identifiers_before_service_access(
    monkeypatch, identifier
):
    factory = Mock()
    monkeypatch.setattr(cli, "public_requester", factory)
    with pytest.raises(SystemExit):
        cli.main(["remove", "movie", identifier])
    factory.assert_not_called()


def test_owner_removal_result_reaches_the_cli(monkeypatch, capsys):
    monkeypatch.setenv("ARR_MEDIA_OPERATOR_DISCORD_USER_ID", "owner")
    monkeypatch.setenv(
        "CLAWDE_CHANNEL_PROMPT", '{"source":"discord","user_id":"owner"}'
    )
    monkeypatch.setattr(cli, "public_requester", lambda *_: "client")
    remove = Mock(return_value={"result": "media_removed"})
    monkeypatch.setattr(cli, "remove_media", remove)
    assert cli.main(["remove", "movie", "769"]) == 0
    assert json.loads(capsys.readouterr().out)["result"] == "media_removed"
    assert remove.call_args.args[0] == "client"


def test_partial_removal_never_claims_success(monkeypatch, capsys):
    monkeypatch.setenv("ARR_MEDIA_OPERATOR_DISCORD_USER_ID", "owner")
    monkeypatch.setenv(
        "CLAWDE_CHANNEL_PROMPT", '{"source":"discord","user_id":"owner"}'
    )
    monkeypatch.setattr(cli, "public_requester", lambda *_: "client")
    monkeypatch.setattr(
        cli, "remove_media", Mock(side_effect=ValueError("unconfirmed"))
    )
    assert cli.main(["remove", "movie", "769"]) == 1
    captured = capsys.readouterr()
    assert not captured.out
    assert "unconfirmed; no success confirmed" in captured.err
