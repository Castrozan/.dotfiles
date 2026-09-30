import json
from pathlib import Path
import sys
import tempfile
import tomllib

import tomli_w


def seed_profile(source_path: Path, profile_path: Path) -> None:
    configuration = tomllib.loads(source_path.read_text())
    try:
        current_configuration = tomllib.loads(profile_path.read_text())
    except FileNotFoundError:
        current_configuration = {}
    for setting in ("model", "model_reasoning_effort"):
        if setting not in configuration and setting in current_configuration:
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
    directory = Path(sys.argv[1])
    sources = json.loads(Path(sys.argv[2]).read_text())
    for name, source in sources.items():
        seed_profile(Path(source), directory / f"{name}.config.toml")


if __name__ == "__main__":
    main()
