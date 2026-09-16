import json


def permission_decision(result):
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)["hookSpecificOutput"].get("permissionDecision")


def permission_reason(result):
    if not result.stdout.strip():
        return ""
    return json.loads(result.stdout)["hookSpecificOutput"].get(
        "permissionDecisionReason", ""
    )


def assert_blocked(result):
    assert result.returncode == 0
    assert permission_decision(result) == "deny"


def assert_allowed(result):
    assert result.returncode == 0
    assert result.stdout == ""
