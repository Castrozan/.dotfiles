import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from native_opencode_profile import prepare_profile, run_native


COMMON_PERMISSIONS = dict.fromkeys(
    ("read", "grep", "glob", "bash", "skill", "todowrite", "question"), "allow"
)
AGENT_PERMISSIONS = {
    "software-engineer": {"*": "deny", **COMMON_PERMISSIONS, "edit": "allow"},
    "quality-assurance": {"*": "deny", **COMMON_PERMISSIONS},
    "explore": {"*": "allow", "edit": "deny"},
}


def verify_agent(result, name, source, profile):
    assert result.returncode == 0, result.stderr
    agent = json.loads(result.stdout)
    assert agent["name"] == name and agent["mode"] == "subagent", agent
    assert agent["prompt"] == source.read_text().split("\n---\n", 1)[1].strip(), agent
    expected = AGENT_PERMISSIONS[name]
    rules = agent["permission"]
    automatic = rules[-1]
    assert (
        automatic["permission"] == "external_directory"
        and automatic["action"] == "allow"
    ), automatic
    assert automatic["pattern"] == str(profile / "data/opencode/tool-output/*"), (
        automatic
    )
    rules = rules[-len(expected) - 1 : -1]
    assert len(rules) == len(expected) and all(
        rule["pattern"] == "*" for rule in rules
    ), rules
    assert rules[0] == {"permission": "*", "pattern": "*", "action": expected["*"]}, (
        rules
    )
    assert {rule["permission"]: rule["action"] for rule in rules} == expected, rules


def verify_tool(executable, environment, workspace, name, tool, arguments, allowed):
    result = run_native(
        executable,
        environment,
        workspace,
        name,
        "--tool",
        tool,
        "--params",
        json.dumps(arguments),
    )
    if allowed:
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)
    assert result.returncode != 0 and "disabled for agent" in result.stderr, result
    return None


def verify_positive(executable, sources, root):
    environment, workspace = prepare_profile(root, sources)
    for name in AGENT_PERMISSIONS:
        verify_agent(
            run_native(executable, environment, workspace, name),
            name,
            sources / f"{name}.md",
            root,
        )
    marker = workspace / "owned-marker.txt"
    verify_tool(
        executable,
        environment,
        workspace,
        "software-engineer",
        "write",
        {"filePath": str(marker), "content": "native-write-control\n"},
        True,
    )
    assert marker.read_text() == "native-write-control\n"
    result = verify_tool(
        executable,
        environment,
        workspace,
        "software-engineer",
        "read",
        {"filePath": str(marker)},
        True,
    )
    assert "native-write-control" in json.dumps(result)
    for name in ("quality-assurance", "explore"):
        absent_marker = workspace / f"{name}-forbidden.txt"
        verify_tool(
            executable,
            environment,
            workspace,
            name,
            "write",
            {"filePath": str(absent_marker), "content": "forbidden\n"},
            False,
        )
        assert not absent_marker.exists()
        verify_tool(
            executable,
            environment,
            workspace,
            name,
            "edit",
            {
                "filePath": str(marker),
                "oldString": "native-write-control",
                "newString": "forbidden",
            },
            False,
        )
        assert marker.read_text() == "native-write-control\n"


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
    result = run_native(executable, environment, workspace, name)
    if result.returncode == 0:
        agent = json.loads(result.stdout)
        assert agent["description"] == "Ambient control", agent
        if not corruption:
            assert agent["prompt"] == "AMBIENT_ONLY_AGENT", agent
    try:
        verify_agent(result, name, sources / f"{name}.md", root / "profile")
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
        "Verified 3 native agents, 6 native tool cases and 6 ambient-fallback controls"
    )


if __name__ == "__main__":
    main()
