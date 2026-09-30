import json
from pathlib import Path
import re
import sys
import tempfile
import tomllib

import tomli_w

from codex_runtime_configuration import merge_runtime_preserved_configuration


NIX_STORE = Path("/nix/store")


def nix_store_file(argument: str) -> Path:
    path = Path(argument).resolve(strict=True)
    if not path.is_relative_to(NIX_STORE) or not path.is_file():
        raise ValueError("Profile sources must be files in the Nix store")
    return path


def seed_profile(source_path: Path, profile_path: Path) -> None:
    source_configuration = tomllib.loads(source_path.read_text())
    try:
        current_configuration = tomllib.loads(profile_path.read_text())
    except FileNotFoundError:
        current_configuration = {}
    configuration = merge_runtime_preserved_configuration(
        source_configuration, current_configuration
    )
    for setting in ("model", "model_reasoning_effort"):
        if setting in source_configuration:
            configuration[setting] = source_configuration[setting]
        elif setting in current_configuration:
            configuration[setting] = current_configuration[setting]
    content = tomli_w.dumps(configuration).encode()
    if (
        not profile_path.is_symlink()
        and profile_path.exists()
        and profile_path.read_bytes() == content
    ):
        profile_path.chmod(0o600)
        return
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=profile_path.parent, delete=False) as stream:
        temporary_path = Path(stream.name)
        try:
            stream.write(content)
            stream.flush()
            temporary_path.replace(profile_path)
        finally:
            temporary_path.unlink(missing_ok=True)


def main() -> None:
    directory = Path.home() / ".codex"
    if Path(sys.argv[1]).resolve() != directory.resolve():
        raise ValueError("Profiles must be written to the managed Codex directory")
    sources = json.loads(nix_store_file(sys.argv[2]).read_text())
    for name, source in sources.items():
        if not re.fullmatch(r"dotfiles-[A-Za-z0-9_-]+", name):
            raise ValueError("Invalid managed Codex profile name")
        seed_profile(nix_store_file(source), directory / f"{name}.config.toml")


if __name__ == "__main__":
    main()
