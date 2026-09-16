import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from instructions.ai_instruction_format import InstructionInspection
from instructions.instruction_surface_scanner import REPO_ROOT

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


def skill_reference_references(
    path: Path, inspection: InstructionInspection
) -> list[str]:
    skill_directory = owning_skill_directory(path)
    if skill_directory is None:
        return []
    references = []
    for link in inspection.links:
        destination = urlsplit(urljoin(path.absolute().as_uri(), link.target))
        target = Path(unquote(destination.path))
        if destination.scheme == "file" and target.is_relative_to(
            skill_directory / "references"
        ):
            references.append(target.relative_to(skill_directory).as_posix())
    return references


def noncanonical_skill_reference_paths(
    path: Path, inspection: InstructionInspection
) -> list[str]:
    references = [
        token
        for token in backticked_path_tokens(path.read_text())
        if REFERENCE_PATH.search(token)
    ]
    for link in inspection.links:
        destination = urlsplit(link.target)
        if "references" in Path(destination.path).parts and (
            destination.scheme == "file"
            or (
                not destination.scheme
                and destination.path.startswith(("/", *REPOSITORY_TOP_LEVEL_PREFIXES))
            )
        ):
            references.append(link.target)
    return references


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
