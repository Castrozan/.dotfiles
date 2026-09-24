import json
import runpy
from pathlib import Path

import pytest


register_plugin = runpy.run_path(
    Path(__file__).parents[2] / "scripts/register-managed-plugin.py"
)["register_plugin"]


def test_new_store_revision_replaces_only_the_owned_marketplace(tmp_path, monkeypatch):
    previous = tmp_path / "previous"
    manifest = previous / ".agents/plugins/marketplace.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"plugins": [{"name": "dotfiles"}]}))
    (tmp_path / "config.toml").write_text(
        f'[marketplaces.dotagents-local]\nsource_type="local"\nsource="{previous}"\n'
        '[marketplaces.external]\nsource_type="git"\nsource="https://example.org/repo"\n'
    )
    calls = []
    monkeypatch.setattr(
        "subprocess.run", lambda command, **kwargs: calls.append(command)
    )
    register_plugin(Path("/codex"), tmp_path / "next", tmp_path)
    assert calls == [
        ["/codex", "plugin", "marketplace", "remove", "dotagents-local", "--json"],
        ["/codex", "plugin", "marketplace", "add", str(tmp_path / "next"), "--json"],
        ["/codex", "plugin", "add", "dotfiles@dotagents-local", "--json"],
    ]
    assert "marketplaces.external" in (tmp_path / "config.toml").read_text()


def test_conflicting_marketplace_is_not_removed(tmp_path, monkeypatch):
    previous = tmp_path / "external"
    manifest = previous / ".agents/plugins/marketplace.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"plugins": [{"name": "external"}]}))
    (tmp_path / "config.toml").write_text(
        f'[marketplaces.dotagents-local]\nsource_type="local"\nsource="{previous}"\n'
    )
    calls = []
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError, match="belongs to another source"):
        register_plugin(Path("/codex"), tmp_path / "next", tmp_path)
    assert not calls
