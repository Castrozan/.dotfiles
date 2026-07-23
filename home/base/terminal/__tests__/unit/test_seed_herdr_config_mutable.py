import importlib.util
import pathlib
import tomllib

SEED_SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "herdr"
    / "seed-herdr-config-mutable.py"
)


def _load_seed_module():
    module_spec = importlib.util.spec_from_file_location(
        "seed_herdr_config_mutable", SEED_SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


seed_herdr_config_mutable = _load_seed_module()

NIX_SOURCE_CONFIG = """[ui]
accent = "cyan"
sidebar_collapsed = true

[keys]
prefix = "ctrl+b"

[[keys.command]]
key = "ctrl+g"
type = "shell"
command = "gateway"

[experimental]
allow_nested = true
"""


def _run_main(monkeypatch, tmp_path, live_config_text):
    nix_source_path = tmp_path / "config.toml.nix-source"
    target_path = tmp_path / "config.toml"
    nix_source_path.write_text(NIX_SOURCE_CONFIG)
    if live_config_text is not None:
        target_path.write_text(live_config_text)
    monkeypatch.setenv("HERDR_NIX_SOURCE", str(nix_source_path))
    monkeypatch.setenv("HERDR_CONFIG", str(target_path))
    seed_herdr_config_mutable.main()
    return target_path


def test_seeds_from_nix_source_when_target_absent(monkeypatch, tmp_path):
    target_path = _run_main(monkeypatch, tmp_path, None)
    assert target_path.read_text() == NIX_SOURCE_CONFIG
    assert (target_path.stat().st_mode & 0o777) == 0o600


def test_target_is_writable_after_seeding(monkeypatch, tmp_path):
    target_path = _run_main(monkeypatch, tmp_path, None)
    assert target_path.stat().st_mode & 0o200


def test_preserves_runtime_agent_panel_sort_across_rebuild(monkeypatch, tmp_path):
    live = '[ui]\nagent_panel_sort = "priority"\naccent = "magenta"\n'
    target_path = _run_main(monkeypatch, tmp_path, live)
    merged = tomllib.loads(target_path.read_text())
    assert merged["ui"]["agent_panel_sort"] == "priority"


def test_nix_source_wins_for_declared_ui_keys(monkeypatch, tmp_path):
    monkeypatch.delenv("HERDR_RUNTIME_OWNS_ACCENT", raising=False)
    live = '[ui]\nagent_panel_sort = "priority"\naccent = "magenta"\n'
    target_path = _run_main(monkeypatch, tmp_path, live)
    merged = tomllib.loads(target_path.read_text())
    assert merged["ui"]["accent"] == "cyan"


def test_runtime_accent_preserved_when_runtime_owns_accent(monkeypatch, tmp_path):
    monkeypatch.setenv("HERDR_RUNTIME_OWNS_ACCENT", "1")
    live = '[ui]\nagent_panel_sort = "priority"\naccent = "#abcdef"\n'
    target_path = _run_main(monkeypatch, tmp_path, live)
    merged = tomllib.loads(target_path.read_text())
    assert merged["ui"]["accent"] == "#abcdef"


def test_runtime_accent_reverts_to_nix_source_when_runtime_does_not_own_accent(
    monkeypatch, tmp_path
):
    monkeypatch.delenv("HERDR_RUNTIME_OWNS_ACCENT", raising=False)
    live = '[ui]\nagent_panel_sort = "priority"\naccent = "#abcdef"\n'
    target_path = _run_main(monkeypatch, tmp_path, live)
    merged = tomllib.loads(target_path.read_text())
    assert merged["ui"]["accent"] == "cyan"


def test_declared_keybindings_survive_and_come_from_nix_source(monkeypatch, tmp_path):
    live = '[ui]\nagent_panel_sort = "priority"\n\n[keys]\nprefix = "ctrl+z"\n'
    target_path = _run_main(monkeypatch, tmp_path, live)
    merged = tomllib.loads(target_path.read_text())
    assert merged["keys"]["prefix"] == "ctrl+b"
    assert merged["keys"]["command"][0]["key"] == "ctrl+g"


def test_non_allowlisted_runtime_ui_key_reverts_to_nix_source(monkeypatch, tmp_path):
    live = '[ui]\nagent_panel_sort = "priority"\nsidebar_collapsed = false\n'
    target_path = _run_main(monkeypatch, tmp_path, live)
    merged = tomllib.loads(target_path.read_text())
    assert merged["ui"]["sidebar_collapsed"] is True


def test_no_op_when_nix_source_absent(monkeypatch, tmp_path):
    target_path = tmp_path / "config.toml"
    target_path.write_text('[ui]\nagent_panel_sort = "priority"\n')
    monkeypatch.setenv("HERDR_NIX_SOURCE", str(tmp_path / "missing.nix-source"))
    monkeypatch.setenv("HERDR_CONFIG", str(target_path))
    seed_herdr_config_mutable.main()
    assert 'agent_panel_sort = "priority"' in target_path.read_text()


def test_corrupt_live_config_falls_back_to_nix_source(monkeypatch, tmp_path):
    target_path = _run_main(monkeypatch, tmp_path, "this is not = valid toml [[[")
    assert target_path.read_text() == NIX_SOURCE_CONFIG


def test_output_is_idempotent_across_repeated_runs(monkeypatch, tmp_path):
    live = '[ui]\nagent_panel_sort = "workspaces"\n'
    target_path = _run_main(monkeypatch, tmp_path, live)
    first_output = target_path.read_text()
    monkeypatch.setenv("HERDR_NIX_SOURCE", str(tmp_path / "config.toml.nix-source"))
    monkeypatch.setenv("HERDR_CONFIG", str(target_path))
    seed_herdr_config_mutable.main()
    assert target_path.read_text() == first_output
