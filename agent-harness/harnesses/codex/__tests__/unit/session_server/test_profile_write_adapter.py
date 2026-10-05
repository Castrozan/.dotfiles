import json
import tomllib
from unittest.mock import Mock

import pytest

from profile_write_adapter import CodexProfileWriteAdapter
import profile_write_adapter


@pytest.fixture
def profile(tmp_path):
    path = tmp_path / "interactive.config.toml"
    path.write_text(
        'developer_instructions = "Keep the policy"\nmodel_reasoning_effort = "high"\n[plugins.existing]\nenabled = true\n'
    )
    path.chmod(0o600)
    return path


def request_for(edits, **parameters):
    return json.dumps(
        {
            "id": 42,
            "method": "config/batchWrite",
            "params": {"edits": edits, **parameters},
        }
    )


def edit(key, value):
    return {"keyPath": key, "value": value, "mergeStrategy": "upsert"}


def test_model_and_effort_save_to_profile_after_native_success(profile):
    adapter = CodexProfileWriteAdapter(profile)
    frame = adapter.prepare_request(
        request_for(
            [edit("model", "new-model"), edit("model_reasoning_effort", "medium")]
        )
    )
    assert json.loads(frame)["params"]["edits"] == []
    assert tomllib.loads(profile.read_text())["model_reasoning_effort"] == "high"
    response = adapter.finish_response(
        json.dumps(
            {
                "id": 42,
                "result": {
                    "status": "ok",
                    "filePath": str(profile.parent / "config.toml"),
                    "version": "native-version",
                },
            }
        )
    )
    saved = tomllib.loads(profile.read_text())
    assert saved["model"] == "new-model"
    assert saved["model_reasoning_effort"] == "medium"
    assert saved["developer_instructions"] == "Keep the policy"
    assert saved["plugins"]["existing"]["enabled"] is True
    assert profile.stat().st_mode & 0o777 == 0o600
    assert json.loads(response)["result"]["filePath"] == str(profile)


def test_other_edits_and_native_version_check_are_preserved(profile):
    adapter = CodexProfileWriteAdapter(profile)
    native_edit = edit("tui.animations", False)
    request = json.loads(
        adapter.prepare_request(
            request_for(
                [edit("model", "new-model"), native_edit],
                expectedVersion="v1",
                reloadUserConfig=True,
            )
        )
    )
    assert request["params"] == {
        "edits": [native_edit],
        "expectedVersion": "v1",
        "reloadUserConfig": True,
    }
    response = '{"id":42,"error":{"code":-1,"message":"version conflict"}}'
    assert adapter.finish_response(response) == response
    assert "model" not in tomllib.loads(profile.read_text())


def test_single_value_write_uses_native_batch_acknowledgement(profile):
    adapter = CodexProfileWriteAdapter(profile)
    request = json.loads(
        adapter.prepare_request(
            json.dumps(
                {
                    "id": 42,
                    "method": "config/value/write",
                    "params": edit("model_reasoning_effort", "low"),
                }
            )
        )
    )
    assert request == {"id": 42, "method": "config/batchWrite", "params": {"edits": []}}


@pytest.mark.parametrize("target", [None, "base", "profile", "other"])
def test_native_base_target_routes_profile_settings_but_other_targets_stay_native(
    profile, target
):
    adapter = CodexProfileWriteAdapter(profile)
    file_path = (
        None
        if target is None
        else str(
            profile
            if target == "profile"
            else profile.parent / ("config.toml" if target == "base" else "other.toml")
        )
    )
    frame = request_for([edit("model", "chosen")], filePath=file_path)
    rewritten = adapter.prepare_request(frame)
    assert (rewritten == frame) is (target == "other")
    if target == "profile":
        assert "filePath" not in json.loads(rewritten)["params"]


@pytest.mark.parametrize(
    "frame",
    [
        "invalid JSON",
        '{"method":"thread/name/set","params":{}}',
        '{"method":"config/batchWrite","params":{"edits":[{"keyPath":"tui.animations","value":false,"mergeStrategy":"upsert"}]}}',
    ],
)
def test_unrelated_messages_pass_through(profile, frame):
    assert CodexProfileWriteAdapter(profile).prepare_request(frame) == frame


def test_notifications_and_other_replies_do_not_finish_a_pending_write(profile):
    adapter = CodexProfileWriteAdapter(profile)
    adapter.prepare_request(request_for([edit("model", "chosen")]))
    for frame in (
        '{"method":"thread/name/updated","params":{}}',
        '{"id":19,"result":{}}',
    ):
        assert adapter.finish_response(frame) == frame
    assert "model" not in tomllib.loads(profile.read_text())


def test_invalid_profile_returns_error_without_overwriting_it(profile):
    adapter = CodexProfileWriteAdapter(profile)
    profile.write_text("broken TOML")
    adapter.prepare_request(request_for([edit("model", "chosen")]))
    response = json.loads(adapter.finish_response('{"id":42,"result":{}}'))
    assert "Could not save Codex profile" in response["error"]["message"]
    assert profile.read_text() == "broken TOML"


def test_null_runtime_setting_removes_the_profile_override(profile):
    adapter = CodexProfileWriteAdapter(profile)
    adapter.prepare_request(request_for([edit("model_reasoning_effort", None)]))
    adapter.finish_response('{"id":42,"result":{}}')
    assert "model_reasoning_effort" not in tomllib.loads(profile.read_text())


def test_locked_profile_fails_within_the_write_deadline(profile, monkeypatch):
    monkeypatch.setattr(
        profile_write_adapter.fcntl, "flock", Mock(side_effect=BlockingIOError)
    )
    monkeypatch.setattr(
        profile_write_adapter.time, "monotonic", Mock(side_effect=[0, 2])
    )
    adapter = CodexProfileWriteAdapter(profile)
    adapter.prepare_request(request_for([edit("model", "chosen")]))
    response = json.loads(adapter.finish_response('{"id":42,"result":{}}'))
    assert "locked for 1s" in response["error"]["message"]
    assert "model" not in tomllib.loads(profile.read_text())
