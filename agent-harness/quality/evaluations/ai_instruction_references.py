import re
from pathlib import Path

from instruction_surface_scanner import REPO_ROOT

REPOSITORY_TOP_LEVEL_PREFIXES = (
    "agent-harness/",
    "agents/",
    "home/",
    "machine-configuration/",
    "nixos/",
    "private-configuration/",
    "repository/",
    "hosts/",
    "modules/",
    "overlays/",
)
BACKTICKED_TOKEN = re.compile(r"`([^`\n]+?)`")
REFERENCE_PATH = re.compile(r"references/[a-z0-9][a-z0-9_-]*\.md")
SKILL_RELATIVE_SCRIPT_TOKEN = re.compile(r"scripts/[A-Za-z0-9._/-]+")


def owning_skill_directory(path: Path) -> Path | None:
    for directory in [path.parent, *path.parents]:
        if (directory / "SKILL.md").is_file():
            return directory
    return None


def backticked_path_tokens(text: str) -> list[str]:
    tokens = []
    for matched in BACKTICKED_TOKEN.finditer(text):
        token = matched.group(1).strip()
        if " " in token:
            continue
        tokens.append(token)
    return tokens


def repository_path_references(path: Path) -> list[str]:
    return [
        token
        for token in backticked_path_tokens(path.read_text())
        if token.startswith(REPOSITORY_TOP_LEVEL_PREFIXES)
    ]


def skill_reference_references(path: Path) -> list[str]:
    return [
        token
        for token in backticked_path_tokens(path.read_text())
        if REFERENCE_PATH.fullmatch(token)
    ]


def noncanonical_skill_reference_paths(path: Path) -> list[str]:
    return [
        token
        for token in backticked_path_tokens(path.read_text())
        if REFERENCE_PATH.search(token) and not REFERENCE_PATH.fullmatch(token)
    ]


def skill_relative_script_references(path: Path) -> list[str]:
    return [
        token
        for token in backticked_path_tokens(path.read_text())
        if SKILL_RELATIVE_SCRIPT_TOKEN.fullmatch(token)
    ]


def unresolved_skill_relative_scripts(path: Path) -> list[str]:
    skill_directory = owning_skill_directory(path)
    if skill_directory is None:
        return []
    return [
        token
        for token in skill_relative_script_references(path)
        if not (skill_directory / token).exists()
    ]


def unresolved_repository_paths(path: Path) -> list[str]:
    return [
        token
        for token in repository_path_references(path)
        if "<" not in token and ">" not in token
        if not (REPO_ROOT / token.split(":")[0]).exists()
    ]


def unresolved_skill_references(path: Path) -> list[str]:
    skill_directory = owning_skill_directory(path)
    if skill_directory is None:
        return []
    return [
        token
        for token in skill_reference_references(path)
        if not (skill_directory / token).is_file()
    ]
