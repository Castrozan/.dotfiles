from pathlib import Path


CODEX_MODULE_DIRECTORY = Path(__file__).parents[2]


def test_codex_launcher_bypasses_hook_trust_for_declared_hooks():
    launcher_source = (CODEX_MODULE_DIRECTORY / "scripts" / "codex").read_text()

    assert "--dangerously-bypass-hook-trust" in launcher_source


def test_codex_disables_self_update_banner():
    config_source = (CODEX_MODULE_DIRECTORY / "config.nix").read_text()

    assert "check_for_update_on_startup = false;" in config_source
