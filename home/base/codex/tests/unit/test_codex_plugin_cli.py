import codex_plugin_cli
from codex_plugin_cli import (
    ported_marketplace_is_registered,
    previously_ported_plugin_names,
)

CONFIG_WITH_PORTED_MARKETPLACE = """
[marketplaces.claude-code-ports]
source_type = "local"

[marketplaces.openai-curated]
source_type = "local"

[plugins."mcd-ca-ai-workspace@claude-code-ports"]
enabled = true

[plugins."figma@openai-curated"]
enabled = true
"""

CONFIG_WITHOUT_PORTED_MARKETPLACE = """
[marketplaces.openai-curated]
source_type = "local"
"""


def _write_config(tmp_path, monkeypatch, contents):
    config_path = tmp_path / "config.toml"
    config_path.write_text(contents)
    monkeypatch.setattr(codex_plugin_cli, "codex_config_path", config_path)


def test_previously_ported_plugin_names_only_returns_ported_marketplace(
    tmp_path, monkeypatch
):
    _write_config(tmp_path, monkeypatch, CONFIG_WITH_PORTED_MARKETPLACE)

    assert previously_ported_plugin_names() == {"mcd-ca-ai-workspace"}


def test_previously_ported_plugin_names_missing_config_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(codex_plugin_cli, "codex_config_path", tmp_path / "absent.toml")

    assert previously_ported_plugin_names() == set()


def test_ported_marketplace_is_registered_true(tmp_path, monkeypatch):
    _write_config(tmp_path, monkeypatch, CONFIG_WITH_PORTED_MARKETPLACE)

    assert ported_marketplace_is_registered() is True


def test_ported_marketplace_is_registered_false_when_absent(tmp_path, monkeypatch):
    _write_config(tmp_path, monkeypatch, CONFIG_WITHOUT_PORTED_MARKETPLACE)

    assert ported_marketplace_is_registered() is False
