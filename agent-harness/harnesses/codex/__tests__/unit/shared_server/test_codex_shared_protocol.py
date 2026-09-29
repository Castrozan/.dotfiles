from uuid import uuid4

import pytest

from codex_client_context import ClientContext, ContextConflict, read_context
from codex_client_configuration import thread_configuration
from codex_client_protocol import ClientProtocol


def thread_reply(identifier, request=1, ephemeral=False):
    return {
        "id": request,
        "result": {"thread": {"id": identifier, "ephemeral": ephemeral}},
    }


def test_persistent_start_binds_before_response_but_title_threads_do_not(tmp_path):
    context = ClientContext(tmp_path, {"HERDR_PANE_ID": "pane"})
    protocol = ClientProtocol(context, {"developer_instructions": "interactive"}, {})
    persistent, ephemeral = str(uuid4()), str(uuid4())
    try:
        request = protocol.request({"id": 1, "method": "thread/start", "params": {}})
        assert "developer_instructions" not in request["params"]["config"]
        response = protocol.response(thread_reply(persistent))
        assert (
            read_context(tmp_path, response["result"]["thread"]["id"])["environment"][
                "HERDR_PANE_ID"
            ]
            == "pane"
        )
        request = protocol.request(
            {"id": 2, "method": "thread/start", "params": {"ephemeral": True}}
        )
        assert request["params"] == {"ephemeral": True}
        protocol.response(thread_reply(ephemeral, 2, True))
        assert read_context(tmp_path, ephemeral) is None
    finally:
        protocol.close()
    assert read_context(tmp_path, persistent) is None


def test_failed_resume_releases_ownership_and_does_not_steal_an_attachment(tmp_path):
    identifier = str(uuid4())
    first = ClientProtocol(ClientContext(tmp_path, {"HERDR_PANE_ID": "first"}), {}, {})
    second = ClientProtocol(
        ClientContext(tmp_path, {"HERDR_PANE_ID": "second"}), {}, {}
    )
    request = {"id": 1, "method": "thread/resume", "params": {"threadId": identifier}}
    try:
        first.request(request)
        with pytest.raises(ContextConflict):
            second.request(request)
        first.response({"id": 1, "error": {"code": -1}})
        second.request(request)
        second.response(thread_reply(identifier))
        assert (
            read_context(tmp_path, identifier)["environment"]["HERDR_PANE_ID"]
            == "second"
        )
    finally:
        first.close()
        second.close()


def test_unattached_turns_and_commands_are_refused(tmp_path):
    protocol = ClientProtocol(ClientContext(tmp_path, {}), {}, {})
    for method in ("turn/start", "thread/compact/start", "thread/shellCommand"):
        with pytest.raises(ContextConflict):
            protocol.request(
                {"id": 1, "method": method, "params": {"threadId": str(uuid4())}}
            )


def test_configuration_preserves_native_exclusions_and_explicit_overrides():
    parameters = {
        "config": {"shell_environment_policy": {"set": {"USER_KEY": "explicit"}}}
    }
    resolved = {
        "shell_environment_policy": {
            "ignore_default_excludes": False,
            "exclude": ["workspace_*"],
        }
    }
    result = thread_configuration(
        parameters,
        {},
        {
            "PATH": "/client/bin",
            "API_KEY": "secret",
            "workspace_token": "private",
            "WORKSPACE_NAME": "hidden",
            "HERDR_PANE_ID": "correct",
        },
        resolved,
    )
    policy = result["config"]["shell_environment_policy"]
    assert policy["inherit"] == "none"
    assert policy["set"] == {
        "PATH": "/client/bin",
        "HERDR_PANE_ID": "correct",
        "USER_KEY": "explicit",
    }
    assert parameters["config"]["shell_environment_policy"]["set"] == {
        "USER_KEY": "explicit"
    }


@pytest.mark.parametrize(
    "inherit,expected", [("none", {}), ("core", {"PATH": "client"})]
)
def test_inheritance_policy_does_not_gain_additional_variables(inherit, expected):
    result = thread_configuration(
        {},
        {"shell_environment_policy": {"inherit": inherit}},
        {"PATH": "client", "EXTRA": "hidden"},
    )
    assert result["config"]["shell_environment_policy"]["set"] == expected


def test_canonical_filters_keep_include_rules_for_native_final_filtering():
    result = thread_configuration(
        {},
        {
            "shell_environment_policy": {
                "filters": {"*token*": "exclude", "PATH": "include"},
            }
        },
        {"MyToken": "hidden", "PATH": "client", "USER": "person"},
    )
    policy = result["config"]["shell_environment_policy"]
    assert "MyToken" not in policy["set"]
    assert policy["filters"]["PATH"] == "include"
