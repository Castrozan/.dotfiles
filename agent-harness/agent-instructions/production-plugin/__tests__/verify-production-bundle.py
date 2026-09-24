import hashlib
import json
import stat
import sys
from pathlib import Path


def identities(root: Path):
    paths = root.rglob("*") if root.is_dir() else [root]
    return {
        str(path.relative_to(root)) if root.is_dir() else "": (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            bool(path.stat().st_mode & stat.S_IXUSR),
        )
        for path in paths
        if path.is_file()
    }


def verify(bundle: Path) -> None:
    package = bundle / "plugin"
    inventory = json.loads((package / "artifact-inventory.json").read_text())
    recorded = {}
    for artifact in inventory["artifacts"]:
        source = Path(artifact["source"])
        target = package / artifact["name"]
        expected = identities(source)
        assert expected, f"Empty source artifact: {source}"
        assert identities(target) == expected, f"Artifact changed: {artifact['name']}"
        for relative in expected:
            name = str(Path(artifact["name"]) / relative)
            assert name not in recorded, f"Artifact collision: {name}"
            recorded[name] = source

    generated = {
        "plugin.json",
        ".claude-plugin/plugin.json",
        "artifact-inventory.json",
        ".codex-plugin/plugin.json",
        ".codex-plugin/plugin.json.dotagents-managed",
        ".dotagents-managed",
        ".dotagents-native-fallbacks",
    }
    assert set(identities(package)) == set(recorded) | generated
    discovered = {
        directory.name
        for directory in (package / "skills").iterdir()
        if (directory / "SKILL.md").is_file()
    }
    assert discovered == set(inventory["discovery"]["skills"])
    indexed = set(inventory["discovery"]["indexedSkills"])
    repository = set(inventory["discovery"]["repositorySkills"])
    assert not discovered & (indexed | repository)
    assert not indexed & repository
    for name in indexed | repository:
        assert (package / "library/skills" / name / "SKILL.md").is_file()

    mcp = json.loads((package / "mcp.json").read_text())
    assert mcp["$schema"] == "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    for server in mcp["mcpServers"].values():
        command = Path(server["command"])
        assert not command.is_absolute()
        executable = package / command
        assert executable.resolve().is_relative_to(package.resolve())
        assert executable.stat().st_mode & stat.S_IXUSR
    configuration = json.loads((bundle / ".opencode/opencode.jsonc").read_text())
    assert configuration["$schema"] == "https://opencode.ai/config.json"
    assert [Path(path).resolve() for path in configuration["skills"]["paths"]] == [
        (package / "skills").resolve()
    ]
    print(
        f"Verified {len(inventory['artifacts'])} source artifacts and {len(recorded)} files"
    )


if __name__ == "__main__":
    verify(Path(sys.argv[1]))
