import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_TREE = REPO_ROOT / "agents" / "skills"
MAXIMUM_SKILL_DESCRIPTION_LENGTH = 1024
REPOSITORY_TOP_LEVEL_PREFIXES = (
    "agents/",
    "home/",
    "nixos/",
    "flake/",
    "__tests__/",
    "hosts/",
    "modules/",
    "overlays/",
)
BACKTICKED_TOKEN = re.compile(r"`([^`\n]+?)`")
STANDALONE_XML_TAG = re.compile(r"^<(/?)([a-z][a-z0-9_]*)>\s*$", re.M)
FRONTMATTER_KEY_VALUE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")
SIBLING_CHAPTER_TOKEN = re.compile(r"[A-Za-z0-9._-]+\.md")
SKILL_RELATIVE_SCRIPT_TOKEN = re.compile(r"scripts/[A-Za-z0-9._/-]+")


def skill_definition_files() -> list[Path]:
    return sorted(SKILL_TREE.glob("**/SKILL.md"))


def skill_chapter_files() -> list[Path]:
    return sorted(
        path for path in SKILL_TREE.glob("**/*.md") if path.name != "SKILL.md"
    )


def instruction_surface_files() -> list[Path]:
    surfaces = [
        REPO_ROOT / "agents" / "core_rules" / "core.md",
        REPO_ROOT / "agents" / "dotfiles.md",
    ]
    surfaces += sorted((REPO_ROOT / "agents" / "snippets").glob("*.md"))
    surfaces += sorted(
        (REPO_ROOT / "agents" / "core_rules" / "communication").glob("*.md")
    )
    surfaces += sorted((REPO_ROOT / "agents" / "commands").glob("**/*.md"))
    return surfaces


def every_linted_markdown_file() -> list[Path]:
    return (
        instruction_surface_files() + skill_definition_files() + skill_chapter_files()
    )


def frontmatter_block(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    closing = text.find("\n---", 3)
    if closing == -1:
        return None
    return text[4:closing]


def frontmatter_key_values(text: str) -> dict[str, str] | None:
    block = frontmatter_block(text)
    if block is None:
        return None
    key_values = {}
    for line in block.splitlines():
        matched = FRONTMATTER_KEY_VALUE.match(line)
        if matched:
            key_values[matched.group(1)] = matched.group(2).strip()
        elif line.strip():
            return None
    return key_values


def xml_tag_structure_error(text: str) -> str | None:
    open_tags = []
    for matched in STANDALONE_XML_TAG.finditer(text):
        is_closing, tag_name = matched.group(1), matched.group(2)
        if not is_closing:
            open_tags.append(tag_name)
            continue
        if not open_tags:
            return f"closing </{tag_name}> with no open tag"
        if open_tags[-1] != tag_name:
            return f"closing </{tag_name}> while <{open_tags[-1]}> is still open"
        open_tags.pop()
    if open_tags:
        return f"unclosed <{open_tags[-1]}>"
    return None


def unclosed_code_fence_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("```")) % 2


def backticked_path_tokens(text: str) -> list[str]:
    tokens = []
    for matched in BACKTICKED_TOKEN.finditer(text):
        token = matched.group(1).strip()
        if " " in token or token.startswith("/"):
            continue
        tokens.append(token)
    return tokens


def repository_path_references(path: Path) -> list[str]:
    return [
        token
        for token in backticked_path_tokens(path.read_text())
        if token.startswith(REPOSITORY_TOP_LEVEL_PREFIXES)
    ]


def sibling_chapter_references(path: Path) -> list[str]:
    return [
        token
        for token in backticked_path_tokens(path.read_text())
        if SIBLING_CHAPTER_TOKEN.fullmatch(token)
    ]


def skill_relative_script_references(path: Path) -> list[str]:
    return [
        token
        for token in backticked_path_tokens(path.read_text())
        if SKILL_RELATIVE_SCRIPT_TOKEN.fullmatch(token)
    ]


def unresolved_skill_relative_scripts(path: Path) -> list[str]:
    return [
        token
        for token in skill_relative_script_references(path)
        if not (path.parent / token).exists()
    ]


def unresolved_repository_paths(path: Path) -> list[str]:
    return [
        token
        for token in repository_path_references(path)
        if not (REPO_ROOT / token.split(":")[0]).exists()
    ]


def unresolved_sibling_chapters(path: Path) -> list[str]:
    return [
        token
        for token in sibling_chapter_references(path)
        if not (path.parent / token).exists()
    ]
