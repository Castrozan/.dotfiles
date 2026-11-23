import yaml

from instructions.instruction_surface_scanner import (
    REPO_ROOT,
    frontmatter_block,
    public_skill_definition_path,
    subagent_definition_files,
)

SUBAGENT_TREE = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "rulesync"
    / "sources"
    / "subagents"
)


def subagent_frontmatter():
    entries = []
    for definition in subagent_definition_files():
        metadata = yaml.safe_load(frontmatter_block(definition.read_text())) or {}
        entries.append((definition, metadata | metadata.get("claudecode", {})))
    return entries


def label(definition):
    return str(definition.relative_to(REPO_ROOT))


def name_mismatches(entries):
    return [
        f"{label(definition)} declares '{keys.get('name')}'"
        for definition, keys in entries
        if (keys.get("name") or "").lower() != definition.stem.lower()
    ]


def definitions_without_a_model(entries):
    return [label(definition) for definition, keys in entries if not keys.get("model")]


def definitions_without_a_tool_policy(entries):
    return [
        label(definition)
        for definition, keys in entries
        if not keys.get("tools") and not keys.get("disallowedTools")
    ]


def unresolved_skill_bindings(entries):
    unresolved = []
    for definition, keys in entries:
        for skill_name in (keys.get("skills") or "").split(","):
            skill_name = skill_name.strip()
            if skill_name and public_skill_definition_path(skill_name) is None:
                unresolved.append(f"{label(definition)} -> {skill_name}")
    return unresolved


def test_every_skill_a_subagent_binds_exists_on_disk():
    unresolved = unresolved_skill_bindings(subagent_frontmatter())
    assert not unresolved, (
        "these subagents bind skills that do not exist, so the agent loads nothing "
        "and improvises from ambient context while the definition still reads as "
        "though the method were attached: " + ", ".join(unresolved)
    )


def test_the_subagent_scan_covers_the_declared_roster():
    names = {keys.get("name") for _, keys in subagent_frontmatter()}
    assert {"software-engineer", "quality-assurance", "explore"} <= names, (
        f"the roster the delivery process names is not what is on disk: {names}"
    )
