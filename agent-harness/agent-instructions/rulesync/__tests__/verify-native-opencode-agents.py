import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from native_model_server import native_model_server
from native_opencode_profile import prepare_profile
from native_opencode_server import native_server


COMMON_PERMISSIONS = dict.fromkeys(
    ("read", "grep", "glob", "shell", "skill", "todowrite", "question"), "allow"
)
AGENT_PERMISSIONS = {
    "software-engineer": {"*": "deny", **COMMON_PERMISSIONS, "edit": "allow"},
    "quality-assurance": {"*": "deny", **COMMON_PERMISSIONS},
    "explore": {"*": "allow", "edit": "deny"},
}


def verify_agent(agent, name, source):
    assert agent["id"] == name and agent["mode"] == "subagent", agent
    assert agent["system"] == source.read_text().split("\n---\n", 1)[1].strip(), agent
    expected = AGENT_PERMISSIONS[name]
    rules = agent["permissions"][-len(expected) :]
    assert all(rule["resource"] == "*" for rule in rules), rules
    assert {rule["action"]: rule["effect"] for rule in rules} == expected, rules


def verify_tool(server, name, tool, arguments, allowed):
    session = server.request(
        "/api/session",
        {
            "agent": name,
            "title": "Native acceptance",
            "model": {"providerID": "acceptance", "id": "fixture"},
            "location": {"directory": server.directory},
        },
    )["data"]["id"]
    server.request(
        f"/api/session/{session}/prompt",
        {"text": json.dumps({"tool": tool, "input": arguments})},
    )
    server.request(f"/api/experimental/session/{session}/wait", {}, method="POST")
    messages = server.request(f"/api/session/{session}/message")["data"]
    calls = [
        content
        for message in messages
        if message["type"] == "assistant"
        for content in message["content"]
        if content["type"] == "tool"
    ]
    assert calls, messages
    status = calls[0]["state"]["status"]
    assert status == ("completed" if allowed else "error"), calls
    return calls[0]


def verify_positive(executable, sources, root):
    with native_model_server() as model:
        environment, workspace = prepare_profile(
            root, sources, model_url=f"http://127.0.0.1:{model.server_port}/v1"
        )
        with native_server(executable, environment, workspace) as server:
            for name in AGENT_PERMISSIONS:
                agent = server.request(f"/api/agent/{name}", location=True)["data"]
                verify_agent(agent, name, sources / f"{name}.md")
            marker = workspace / "owned-marker.txt"
            verify_tool(
                server,
                "software-engineer",
                "write",
                {"path": str(marker), "content": "native-write-control\n"},
                True,
            )
            assert marker.read_text() == "native-write-control\n"
            result = verify_tool(
                server, "software-engineer", "read", {"path": str(marker)}, True
            )
            assert "native-write-control" in json.dumps(result)
            for name in ("quality-assurance", "explore"):
                absent_marker = workspace / f"{name}-forbidden.txt"
                verify_tool(
                    server,
                    name,
                    "write",
                    {"path": str(absent_marker), "content": "forbidden\n"},
                    False,
                )
                assert not absent_marker.exists()
                verify_tool(
                    server,
                    name,
                    "edit",
                    {
                        "path": str(marker),
                        "oldString": "native-write-control",
                        "newString": "forbidden",
                    },
                    False,
                )
                assert marker.read_text() == "native-write-control\n"
            assert model.requests


def verify_negative(executable, sources, root, name, corruption):
    altered_sources = root / "emitted"
    altered_sources.mkdir(parents=True)
    for source in sources.glob("*.md"):
        if source.stem != name:
            (altered_sources / source.name).symlink_to(source.resolve())
    if corruption:
        (altered_sources / f"{name}.md").write_text(
            "---\npermission: [invalid\n---\nCORRUPT_AGENT\n"
        )
    environment, workspace = prepare_profile(
        root / "profile", altered_sources, ambient_names=AGENT_PERMISSIONS
    )
    with native_server(executable, environment, workspace) as server:
        try:
            agent = server.request(f"/api/agent/{name}", location=True)["data"]
            verify_agent(agent, name, sources / f"{name}.md")
        except AssertionError:
            return
    raise AssertionError(f"Invalid emitted {name} passed through ambient fallback")


def identities(sources):
    return {
        source.name: hashlib.sha256(source.read_bytes()).hexdigest()
        for source in sources.glob("*.md")
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("configuration", type=Path)
    arguments = parser.parse_args()
    executable = arguments.executable.resolve(strict=True)
    sources = arguments.configuration.resolve(strict=True) / "opencode/.opencode/agents"
    assert {path.stem for path in sources.glob("*.md")} == set(AGENT_PERMISSIONS)
    original = identities(sources)
    with tempfile.TemporaryDirectory(prefix="rulesync-native-opencode-") as temporary:
        root = Path(temporary).resolve()
        try:
            verify_positive(executable, sources, root / "positive")
            for name in AGENT_PERMISSIONS:
                for corruption in (False, True):
                    verify_negative(
                        executable,
                        sources,
                        root / f"{name}-{corruption}",
                        name,
                        corruption,
                    )
        finally:
            for directory in root.rglob("*"):
                if directory.is_dir() and not directory.is_symlink():
                    directory.chmod(0o755)
    assert original == identities(sources)
    print(
        "Verified 3 native V2 agents, 6 native tool cases and 6 ambient-fallback controls"
    )


if __name__ == "__main__":
    main()
