import os
import pathlib


legacy_profile_names = ("fast", "deep", "web")
codex_config_path = pathlib.Path(
    os.environ.get("CODEX_CONFIG", "~/.codex/config.toml")
).expanduser()
nix_source_path = pathlib.Path(
    os.environ.get("NIX_SOURCE", "~/.codex/config.toml.nix-source")
).expanduser()


def replace_live_config_with_nix_source() -> None:
    source_content = nix_source_path.read_bytes()
    if codex_config_path.exists() and codex_config_path.read_bytes() == source_content:
        codex_config_path.chmod(0o600)
        return

    codex_config_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_config_path = codex_config_path.with_name(
        f".{codex_config_path.name}.tmp"
    )
    try:
        temporary_config_path.write_bytes(source_content)
        temporary_config_path.chmod(0o600)
        temporary_config_path.replace(codex_config_path)
    finally:
        temporary_config_path.unlink(missing_ok=True)


def remove_legacy_generated_profiles() -> None:
    for profile_name in legacy_profile_names:
        profile_path = codex_config_path.parent / f"{profile_name}.config.toml"
        profile_path.unlink(missing_ok=True)


def main() -> int:
    if not nix_source_path.is_file():
        return 0
    replace_live_config_with_nix_source()
    remove_legacy_generated_profiles()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
