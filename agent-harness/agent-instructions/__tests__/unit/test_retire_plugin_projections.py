import importlib.util
import json
from pathlib import Path

import pytest

SOURCE = Path(__file__).parents[2] / "production-plugin/scripts/retire-projections.py"
SPEC = importlib.util.spec_from_file_location("retire_projections", SOURCE)
RETIREMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RETIREMENT)


def replacement(home):
    bundle = home / "bundle"
    (bundle / "plugin").mkdir(parents=True)
    (bundle / "plugin/plugin.json").write_text('{"name":"dotfiles"}')
    return bundle


def test_hermes_preserves_modified_assets_and_retires_only_once(tmp_path):
    bundle = replacement(tmp_path)
    skill = tmp_path / ".hermes/skills/humanize"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("modified instructions")
    (skill / "custom.bin").write_bytes(b"opaque")
    RETIREMENT.retire("hermes", tmp_path, bundle, None)
    assert not skill.exists()
    archived = list(tmp_path.glob(".local/state/agent-plugins/**/custom.bin"))
    assert len(archived) == 1
    assert archived[0].read_bytes() == b"opaque"
    assert (archived[0].parent / "SKILL.md").read_text() == "modified instructions"
    skill.mkdir()
    (skill / "SKILL.md").write_text("deliberate new override")
    RETIREMENT.retire("hermes", tmp_path, bundle, None)
    assert (skill / "SKILL.md").read_text() == "deliberate new override"


def test_missing_replacement_does_not_retire_anything(tmp_path):
    with pytest.raises(ValueError, match="replacement"):
        RETIREMENT.retire("hermes", tmp_path, tmp_path / "missing", None)
    assert not (tmp_path / ".local/state").exists()


@pytest.mark.parametrize(
    "canonical_installed,skill_present", [(True, True), (False, True), (True, False)]
)
def test_repository_backups_leave_discovery_only_after_canonical_installation(
    tmp_path, canonical_installed, skill_present
):
    bundle = replacement(tmp_path)
    names = ["nix", "agent-harness"]
    (bundle / "plugin/artifact-inventory.json").write_text(
        json.dumps({"discovery": {"repositorySkills": names}})
    )
    discovery = tmp_path / ".dotfiles/.opencode/skills"
    discovery.mkdir(parents=True)
    for name in names:
        source = bundle / "plugin/library/skills" / name
        source.mkdir(parents=True)
        if skill_present:
            (source / "SKILL.md").write_text("canonical " + name)
        if canonical_installed:
            (discovery / name).symlink_to(source)
        backup = discovery / (name + ".backup")
        backup.mkdir()
        (backup / "SKILL.md").write_text("old " + name)
        (backup / "opaque.bin").write_bytes(name.encode())
    unrelated = discovery / "unrelated.backup"
    unrelated.mkdir()
    if not canonical_installed or not skill_present:
        with pytest.raises(ValueError, match="canonical"):
            RETIREMENT.retire("repository", tmp_path, bundle, None)
        assert all((discovery / (name + ".backup")).exists() for name in names)
        return
    RETIREMENT.retire("repository", tmp_path, bundle, None)
    RETIREMENT.retire("repository", tmp_path, bundle, None)
    assert unrelated.is_dir()
    for name in names:
        assert not (discovery / (name + ".backup")).exists()
        assert (discovery / name / "SKILL.md").read_text() == "canonical " + name
        archived = list(tmp_path.glob(f".local/state/agent-plugins/**/{name}.backup"))
        assert len(archived) == 1
        assert (archived[0] / "opaque.bin").read_bytes() == name.encode()
        assert (archived[0] / "SKILL.md").read_text() == "old " + name


def test_opencode_removes_only_links_into_retired_root(tmp_path):
    bundle = replacement(tmp_path)
    root = tmp_path / ".config/opencode/claude-plugin-ports"
    root.mkdir(parents=True)
    (root / "old").mkdir()
    skills = root.parent / "skills"
    skills.mkdir()
    (skills / "old").symlink_to(root / "old")
    (skills / "other").symlink_to(bundle)
    RETIREMENT.retire("opencode", tmp_path, bundle, None)
    assert not (skills / "old").is_symlink()
    assert (skills / "other").resolve() == bundle
    assert not root.exists()


def test_foreign_marketplace_is_not_removed(tmp_path):
    bundle = replacement(tmp_path)
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    config.write_text(
        '[marketplaces.claude-code-ports]\nsource_type="local"\nsource="/foreign"\n'
    )
    with pytest.raises(ValueError, match="another source"):
        RETIREMENT.retire("codex", tmp_path, bundle, "/invalid/binary")
    assert "/foreign" in config.read_text()


@pytest.mark.parametrize("marketplace_present", [True, False])
def test_codex_unregisters_only_owned_plugins_before_the_marketplace(
    tmp_path, monkeypatch, marketplace_present
):
    bundle = replacement(tmp_path)
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    root = config.parent / "claude-plugin-ports"
    root.mkdir()
    (root / "asset.bin").write_bytes(b"preserved")
    marketplace_configuration = (
        f'[marketplaces.claude-code-ports]\nsource_type="local"\nsource="{root}"\n'
        if marketplace_present
        else ""
    )
    config.write_text(
        marketplace_configuration + '[plugins."old@claude-code-ports"]\nenabled=true\n'
        '[plugins."other@native"]\nenabled=true\n'
    )
    calls = []
    monkeypatch.setattr(
        RETIREMENT.subprocess,
        "run",
        lambda arguments, **kwargs: calls.append(arguments),
    )
    RETIREMENT.retire("codex", tmp_path, bundle, "codex")
    expected = [
        ["codex", "plugin", "remove", "old@claude-code-ports", "--json"],
    ]
    if marketplace_present:
        expected.append(
            ["codex", "plugin", "marketplace", "remove", "claude-code-ports", "--json"]
        )
    assert calls == expected
    assert not root.exists()
    assert len(list(tmp_path.glob(".local/state/agent-plugins/**/asset.bin"))) == 1
