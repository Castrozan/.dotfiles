import argparse
import json
import os
import subprocess
import tempfile
import tomllib
from pathlib import Path

CODEX_EXECUTABLE = "@codex@"


def archive_projection(source: Path, archive: Path) -> None:
    if not source.exists() and not source.is_symlink():
        return
    archive.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix=source.name + "-", dir=archive))
    source.rename(destination / source.name)


def retire_codex(home: Path, archive: Path) -> None:
    codex_home = home / ".codex"
    configuration_path = codex_home / "config.toml"
    configuration = (
        tomllib.loads(configuration_path.read_text())
        if configuration_path.exists()
        else {}
    )
    name = "claude-code-ports"
    root = codex_home / "claude-plugin-ports"
    marketplace = configuration.get("marketplaces", {}).get(name)
    if marketplace and (
        marketplace.get("source_type") != "local"
        or Path(marketplace.get("source", "")).resolve() != root.resolve()
    ):
        raise ValueError("Retired marketplace name belongs to another source")
    removals = [
        ["remove", "--json", "--", plugin]
        for plugin in configuration.get("plugins", {})
        if plugin.endswith("@" + name)
    ]
    if marketplace:
        removals.append(["marketplace", "remove", "--json", "--", name])
    for arguments in removals:
        subprocess.run(
            [CODEX_EXECUTABLE, "plugin", *arguments],
            env=os.environ | {"CODEX_HOME": str(codex_home)},
            check=True,
            timeout=60,
        )
    archive_projection(root, archive)
    archive_projection(codex_home / "plugins/cache" / name, archive)


def retire_opencode(home: Path, archive: Path) -> None:
    root = home / ".config/opencode/claude-plugin-ports"
    skills = home / ".config/opencode/skills"
    if skills.is_dir():
        for skill in skills.iterdir():
            if skill.is_symlink() and skill.resolve().is_relative_to(root.resolve()):
                skill.unlink()
    archive_projection(root, archive)


def retire_repository_backups(home: Path, bundle: Path, archive: Path) -> None:
    inventory = json.loads((bundle / "plugin/artifact-inventory.json").read_text())
    backups = []
    for harness in (".claude", ".opencode"):
        discovery = home / ".dotfiles" / harness / "skills"
        for name in inventory["discovery"]["repositorySkills"]:
            backup = discovery / (name + ".backup")
            if not backup.exists() and not backup.is_symlink():
                continue
            replacement = discovery / name
            canonical = bundle / "plugin/library/skills" / name
            if (
                not (canonical / "SKILL.md").is_file()
                or not replacement.is_symlink()
                or replacement.resolve() != canonical.resolve()
            ):
                raise ValueError(
                    "Repository skill has no installed canonical replacement"
                )
            backups.append(backup)
    for backup in backups:
        archive_projection(backup, archive)


def retire(target: str, home: Path, bundle: Path) -> None:
    if not (bundle / "plugin/plugin.json").is_file():
        raise ValueError("Complete replacement package is missing")
    archive = home / ".local/state/agent-plugins/retired-projections" / target
    marker = archive / "completed.json"
    if marker.exists():
        return
    if target == "codex":
        retire_codex(home, archive)
    elif target == "opencode":
        retire_opencode(home, archive)
    elif target == "hermes":
        for name in ("humanize", "docs"):
            archive_projection(home / ".hermes/skills" / name, archive)
    elif target == "repository":
        retire_repository_backups(home, bundle, archive)
    archive.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"replacement": str(bundle.resolve())}) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=["codex", "opencode", "hermes", "repository"])
    parser.add_argument("home", type=Path)
    parser.add_argument("bundle", type=Path)
    arguments = parser.parse_args()
    retire(arguments.target, arguments.home, arguments.bundle)
