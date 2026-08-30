import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_TREE = REPO_ROOT / "agent-harness" / "agent-instructions" / "skills"
PRIVATE_MACHINE_SKILL_TREES = sorted(
    (REPO_ROOT / "private-configuration" / "machines").glob("*/skills")
)
SOURCEBOT_SKILL_TREE = (
    REPO_ROOT
    / "machine-configuration"
    / "development"
    / "source-code-search"
    / "sourcebot"
    / "skill"
)
VENDORED_DIRECTORY_NAMES = frozenset({"node_modules", "dist", ".angular"})
FRONTMATTER_KEY_VALUE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")


def is_vendored_dependency_file(path: Path) -> bool:
    return any(part in VENDORED_DIRECTORY_NAMES for part in path.parts)


def every_skill_tree() -> list[Path]:
    return [SKILL_TREE, SOURCEBOT_SKILL_TREE] + PRIVATE_MACHINE_SKILL_TREES


def skill_definition_files() -> list[Path]:
    return sorted(
        {
            path
            for skill_tree in every_skill_tree()
            for path in skill_tree.glob("**/SKILL.md")
            if not is_vendored_dependency_file(path)
        }
    )


def skill_reference_files() -> list[Path]:
    return sorted(
        {
            path
            for skill_file in skill_definition_files()
            for path in (skill_file.parent / "references").glob("**/*.md")
            if not is_vendored_dependency_file(path)
        }
    )


def misplaced_skill_markdown_files() -> list[Path]:
    return sorted(
        path
        for skill_file in skill_definition_files()
        for path in skill_file.parent.glob("*.md")
        if path.name != "SKILL.md"
    )


def subagent_definition_files() -> list[Path]:
    return sorted(
        (REPO_ROOT / "agent-harness" / "agent-instructions" / "subagents").glob("*.md")
    )


def agent_runtime_instruction_files() -> list[Path]:
    public_agents = REPO_ROOT / "agent-harness" / "harnesses" / "clawde" / "agents"
    private_agents = REPO_ROOT / "private-configuration" / "machines"
    patterns = (
        "**/personality.md",
        "**/*-prompt.md",
        "**/*-instructions.md",
        "**/references/*.md",
    )
    return sorted(
        {
            path
            for root in (public_agents, private_agents)
            for pattern in patterns
            for path in root.glob(pattern)
            if "clawde-agents" in path.parts or root == public_agents
        }
    )


def instruction_surface_files() -> list[Path]:
    instruction_root = REPO_ROOT / "agent-harness" / "agent-instructions"
    surfaces = [
        instruction_root / "project-context" / "dotfiles-agent-instructions.md",
    ]
    surfaces += sorted((instruction_root / "core-rules").glob("**/*.md"))
    surfaces += sorted((instruction_root / "rebuild-guidance").glob("*.md"))
    surfaces += sorted((instruction_root / "commands").glob("**/*.md"))
    surfaces += subagent_definition_files()
    surfaces += agent_runtime_instruction_files()
    return surfaces


def every_linted_markdown_file() -> list[Path]:
    return sorted(
        set(
            instruction_surface_files()
            + skill_definition_files()
            + skill_reference_files()
        )
    )


def named_instruction_entrypoint_files() -> list[Path]:
    instruction_root = REPO_ROOT / "agent-harness" / "agent-instructions"
    return sorted(
        set(
            skill_definition_files()
            + subagent_definition_files()
            + [instruction_root / "core-rules" / "core-skill-frontmatter.md"]
        )
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
    current_key = None
    for line in block.splitlines():
        matched = FRONTMATTER_KEY_VALUE.match(line)
        if matched:
            current_key = matched.group(1)
            value = matched.group(2).strip()
            key_values[current_key] = "" if value in {"|", ">", "|-", ">-"} else value
        elif current_key and line.strip():
            key_values[current_key] = " ".join(
                part for part in (key_values[current_key], line.strip()) if part
            )
    return {
        key: value[1:-1]
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}
        else value
        for key, value in key_values.items()
    }
