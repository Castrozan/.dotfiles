import subprocess

import pytest

from staged_rebuild_support import (
    SCRIPTS,
    build_staged_environment,
    read_events,
    write_prepared_request,
)


@pytest.mark.parametrize("action", ["switch", "boot"])
@pytest.mark.parametrize("native_policy", ["true", "false"])
@pytest.mark.parametrize("caller_policy", [None, "true", "false"])
def test_evaluation_inherits_native_ifd_policy_and_preserves_caller_override(
    managed_rebuild_environment, tmp_path, action, native_policy, caller_policy
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    environment["TEST_NATIVE_IFD_POLICY"] = native_policy
    arguments = (
        []
        if caller_policy is None
        else ["--option", "allow-import-from-derivation", caller_policy]
    )
    request = write_prepared_request(tmp_path, action, arguments)
    completed = subprocess.run(
        [str(SCRIPTS / "staged-rebuild"), action, str(request)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )
    effective_policy = native_policy if caller_policy is None else caller_policy
    assert completed.returncode == (0 if effective_policy == "true" else 42)
    evaluation_arguments = next(
        event["arguments"]
        for event in read_events(tmp_path)
        if "eval" in event["arguments"]
    )
    evaluation_policies = [
        evaluation_arguments[position + 2]
        for position, argument in enumerate(evaluation_arguments)
        if argument == "--option"
        and evaluation_arguments[position + 1] == "allow-import-from-derivation"
    ]
    assert evaluation_policies == ([] if caller_policy is None else [caller_policy])
    activation = read_events(tmp_path, "native-events")
    if effective_policy == "true":
        assert [event["phase"] for event in activation] == ["profile", "activate"]
        assert activation[-1]["action"] == action
    else:
        assert not activation
        assert not any(
            "--realise" in event["arguments"]
            and event["arguments"][event["arguments"].index("--realise") + 1].endswith(
                ".drv"
            )
            for event in read_events(tmp_path)
        )
