import json
import runpy
from pathlib import Path

import pytest


register_plugin = runpy.run_path(
    Path(__file__).parents[2] / "scripts/register-managed-plugin.py"
)["register_plugin"]

DOTAGENTS_CATALOG = Path(".agents/plugins/marketplace.json")
CLAUDE_CATALOG = Path(".claude-plugin/marketplace.json")


@pytest.fixture(autouse=True)
def configured_codex(monkeypatch):
    monkeypatch.setitem(register_plugin.__globals__, "CODEX_EXECUTABLE", "/codex")


@pytest.fixture
def recorded_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "subprocess.run", lambda command, **kwargs: calls.append(command)
    )
    return calls


def write_catalog(root, catalog_path, marketplace_name, plugin_names):
    catalog = root / catalog_path
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        json.dumps(
            {
                "name": marketplace_name,
                "plugins": [{"name": plugin_name} for plugin_name in plugin_names],
            }
        )
    )
    return root


def write_dotfiles_bundle(root):
    write_catalog(root, DOTAGENTS_CATALOG, "dotagents-local", ["dotfiles"])
    write_catalog(root, CLAUDE_CATALOG, "dotagents", ["dotfiles"])
    return root


def test_new_store_revision_replaces_only_the_owned_marketplace(
    tmp_path, recorded_calls
):
    previous = write_dotfiles_bundle(tmp_path / "previous")
    following = write_dotfiles_bundle(tmp_path / "next")
    (tmp_path / "config.toml").write_text(
        f'[marketplaces.dotagents-local]\nsource_type="local"\nsource="{previous}"\n'
        '[marketplaces.external]\nsource_type="git"\nsource="https://example.org/repo"\n'
    )
    register_plugin(following, tmp_path)
    assert recorded_calls == [
        [
            "/codex",
            "plugin",
            "marketplace",
            "remove",
            "--json",
            "--",
            "dotagents-local",
        ],
        ["/codex", "plugin", "marketplace", "add", "--json", "--", str(following)],
        ["/codex", "plugin", "add", "--json", "--", "dotfiles@dotagents-local"],
    ]
    assert "marketplaces.external" in (tmp_path / "config.toml").read_text()


def test_a_root_with_only_a_claude_catalog_registers_under_its_own_name(
    tmp_path, recorded_calls
):
    avatar = write_catalog(tmp_path / "avatar", CLAUDE_CATALOG, "avatar", ["avatar"])
    register_plugin(avatar, tmp_path)
    assert recorded_calls == [
        ["/codex", "plugin", "marketplace", "add", "--json", "--", str(avatar)],
        ["/codex", "plugin", "add", "--json", "--", "avatar@avatar"],
    ]


def test_a_pin_bump_replaces_the_previous_revision_of_the_same_plugin(
    tmp_path, recorded_calls
):
    previous = write_catalog(
        tmp_path / "previous", CLAUDE_CATALOG, "avatar", ["avatar"]
    )
    following = write_catalog(tmp_path / "next", CLAUDE_CATALOG, "avatar", ["avatar"])
    (tmp_path / "config.toml").write_text(
        f'[marketplaces.avatar]\nsource_type="local"\nsource="{previous}"\n'
    )
    register_plugin(following, tmp_path)
    assert recorded_calls[0] == [
        "/codex",
        "plugin",
        "marketplace",
        "remove",
        "--json",
        "--",
        "avatar",
    ]
    assert recorded_calls[-1] == [
        "/codex",
        "plugin",
        "add",
        "--json",
        "--",
        "avatar@avatar",
    ]


def test_an_unchanged_root_is_added_again_without_removal(tmp_path, recorded_calls):
    avatar = write_catalog(tmp_path / "avatar", CLAUDE_CATALOG, "avatar", ["avatar"])
    (tmp_path / "config.toml").write_text(
        f'[marketplaces.avatar]\nsource_type="local"\nsource="{avatar}"\n'
    )
    register_plugin(avatar, tmp_path)
    assert [call[2] for call in recorded_calls] == ["marketplace", "add"]


@pytest.mark.parametrize(
    ("source_type", "previous_plugins"),
    [("local", ["external"]), ("git", ["avatar"])],
)
def test_conflicting_marketplace_is_not_removed(
    tmp_path, recorded_calls, source_type, previous_plugins
):
    previous = write_catalog(
        tmp_path / "external", CLAUDE_CATALOG, "avatar", previous_plugins
    )
    following = write_catalog(tmp_path / "next", CLAUDE_CATALOG, "avatar", ["avatar"])
    (tmp_path / "config.toml").write_text(
        f'[marketplaces.avatar]\nsource_type="{source_type}"\nsource="{previous}"\n'
    )
    with pytest.raises(ValueError, match="belongs to another source"):
        register_plugin(following, tmp_path)
    assert not recorded_calls


def test_a_root_without_a_catalog_is_refused_before_any_command(
    tmp_path, recorded_calls
):
    with pytest.raises(ValueError, match="No marketplace catalog"):
        register_plugin(tmp_path / "empty", tmp_path)
    assert not recorded_calls


def test_option_like_root_is_a_resolved_positional_path(
    tmp_path, monkeypatch, recorded_calls
):
    monkeypatch.chdir(tmp_path)
    write_dotfiles_bundle(tmp_path / "--config=features.example=true")
    register_plugin(Path("--config=features.example=true"), tmp_path)
    assert recorded_calls[0] == [
        "/codex",
        "plugin",
        "marketplace",
        "add",
        "--json",
        "--",
        str(tmp_path / "--config=features.example=true"),
    ]
