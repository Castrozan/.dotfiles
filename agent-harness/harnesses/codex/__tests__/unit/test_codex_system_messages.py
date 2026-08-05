from pathlib import Path


CODEX_MODULE_DIRECTORY = Path(__file__).parents[2]


def test_codex_launcher_does_not_bypass_hook_trust():
    package_source = (CODEX_MODULE_DIRECTORY / "package.nix").read_text()

    assert "--dangerously-bypass-hook-trust" not in package_source


def test_codex_disables_self_update_banner():
    config_source = (CODEX_MODULE_DIRECTORY / "config.nix").read_text()

    assert "check_for_update_on_startup = false;" in config_source
