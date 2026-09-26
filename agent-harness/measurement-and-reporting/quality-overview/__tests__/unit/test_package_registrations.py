import json
from pathlib import Path
import subprocess

import pytest


SCRIPTS = Path(__file__).resolve().parents[2]
TARGETS = ("claude", "codex", "opencode", "pi", "hermes")


def fixture_bundle(root):
    package = root / ".agents/plugins/owned"
    (package / "skills").mkdir(parents=True)
    (package / "plugin.json").write_text(json.dumps({"name": "owned"}))
    (root / "plugin").symlink_to(package, target_is_directory=True)
    for target, directory in (
        ("claude", ".claude-plugin"),
        ("codex", ".agents/plugins"),
    ):
        destination = root / directory
        destination.mkdir(parents=True, exist_ok=True)
        source = "./.agents/plugins/owned"
        if target == "codex":
            source = {"source": "local", "path": source}
        (destination / "marketplace.json").write_text(
            json.dumps({"plugins": [{"name": "owned", "source": source}]})
        )
    (root / ".opencode").mkdir()
    (root / ".opencode/opencode.jsonc").write_text(
        json.dumps({"skills": {"paths": [str(package / "skills")]}})
    )
    for target in ("pi", "hermes"):
        destination = root / f".{target}/plugins/owned"
        destination.parent.mkdir(parents=True)
        destination.symlink_to(package, target_is_directory=True)
    return package


def check_registration(root, target):
    return subprocess.run(
        [
            "node",
            str(SCRIPTS / "native_discovery.mjs"),
            "registration",
            target,
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


@pytest.mark.parametrize("target", TARGETS)
def test_registration_requires_the_complete_package_origin(tmp_path, target):
    package = fixture_bundle(tmp_path)
    result = check_registration(tmp_path, target)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["packageRoot"] == str(package.resolve())
    shadow = tmp_path / "shadow"
    shadow.mkdir()
    if target in ("pi", "hermes"):
        destination = tmp_path / f".{target}/plugins/owned"
        destination.unlink()
        destination.symlink_to(shadow, target_is_directory=True)
    elif target == "opencode":
        (tmp_path / ".opencode/opencode.jsonc").write_text(
            json.dumps({"skills": {"paths": [str(shadow)]}})
        )
    else:
        directory = ".claude-plugin" if target == "claude" else ".agents/plugins"
        path = tmp_path / directory / "marketplace.json"
        value = json.loads(path.read_text())
        source = (
            "./shadow"
            if target == "claude"
            else {"source": "local", "path": "./shadow"}
        )
        value["plugins"][0]["source"] = source
        path.write_text(json.dumps(value))
    assert check_registration(tmp_path, target).returncode != 0
