import os
import stat
import subprocess
import sys
import tomllib
from pathlib import Path


SCRIPT_UNDER_TEST = (
    Path(__file__).parents[2] / "config" / "seed_codex_config_mutable.py"
)


def run_seed(tmp_path):
    environment = os.environ.copy()
    environment["HOME"] = str(tmp_path)
    return subprocess.run(
        [sys.executable, str(SCRIPT_UNDER_TEST)],
        check=False,
        env=environment,
        capture_output=True,
        text=True,
    )


def read_live_config(tmp_path):
    with (tmp_path / ".codex" / "config.toml").open("rb") as stream:
        return tomllib.load(stream)


def test_seed_creates_mutable_config_from_nix_source(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        'model = "current-model"\n', encoding="utf-8"
    )

    result = run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    assert read_live_config(tmp_path)["model"] == "current-model"
    assert stat.S_IMODE((codex_directory / "config.toml").stat().st_mode) == 0o600


def test_seed_removes_everything_not_declared_by_nix_source(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        'model = "current-model"\n', encoding="utf-8"
    )
    (codex_directory / "config.toml").write_text(
        'model = "stale-model"\n\n[mcp_servers.stale]\ncommand = "stale"\n',
        encoding="utf-8",
    )

    result = run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    assert read_live_config(tmp_path) == {"model": "current-model"}


def test_seed_removes_legacy_generated_profiles(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        'model = "current-model"\n', encoding="utf-8"
    )
    for profile_name in ("fast", "deep", "web"):
        (codex_directory / f"{profile_name}.config.toml").write_text(
            'model = "stale"\n', encoding="utf-8"
        )

    result = run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    assert not list(codex_directory.glob("*.config.toml"))


def test_seed_is_noop_without_nix_source(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    live_config_path = codex_directory / "config.toml"
    live_config_path.write_text('model = "keep-me"\n', encoding="utf-8")

    result = run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    assert live_config_path.read_text(encoding="utf-8") == 'model = "keep-me"\n'
