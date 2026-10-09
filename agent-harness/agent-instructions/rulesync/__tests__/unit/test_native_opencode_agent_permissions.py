import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def verifier(monkeypatch):
    tests_directory = Path(__file__).resolve().parents[1]
    harness_tests = tests_directory.parents[2] / "harnesses/opencode/__tests__"
    monkeypatch.syspath_prepend(str(tests_directory))
    monkeypatch.syspath_prepend(str(harness_tests))
    specification = importlib.util.spec_from_file_location(
        "native_opencode_agent_verifier",
        tests_directory / "verify-native-opencode-agents.py",
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture
def agent_source(tmp_path):
    source = tmp_path / "agent.md"
    source.write_text("---\nmode: subagent\n---\nNative agent instructions\n")
    return source


def native_agent(verifier, name, browser_effect):
    permissions = [
        {"action": "*", "resource": "*", "effect": "allow"},
        {"action": "read", "resource": "*.env", "effect": "ask"},
        *(
            {"action": action, "resource": "*", "effect": effect}
            for action, effect in verifier.AGENT_PERMISSIONS[name].items()
        ),
    ]
    if browser_effect is not None:
        permissions.append(
            {"action": "browser", "resource": "*", "effect": browser_effect}
        )
    return {
        "id": name,
        "mode": "subagent",
        "system": "Native agent instructions",
        "permissions": permissions,
    }


@pytest.mark.parametrize("name", ("software-engineer", "quality-assurance", "explore"))
def test_native_browser_denial_preserves_declared_agent_permissions(
    verifier, agent_source, name
):
    verifier.verify_agent(native_agent(verifier, name, "deny"), name, agent_source)


@pytest.mark.parametrize("name", ("software-engineer", "quality-assurance", "explore"))
@pytest.mark.parametrize("browser_effect", (None, "allow", "ask"))
def test_missing_or_relaxed_browser_denial_is_rejected(
    verifier, agent_source, name, browser_effect
):
    with pytest.raises(AssertionError):
        verifier.verify_agent(
            native_agent(verifier, name, browser_effect), name, agent_source
        )


@pytest.mark.parametrize("name", ("software-engineer", "quality-assurance", "explore"))
def test_later_browser_permission_override_is_rejected(verifier, agent_source, name):
    agent = native_agent(verifier, name, "deny")
    agent["permissions"].append(
        {"action": "browser", "resource": "*", "effect": "allow"}
    )
    with pytest.raises(AssertionError):
        verifier.verify_agent(agent, name, agent_source)
