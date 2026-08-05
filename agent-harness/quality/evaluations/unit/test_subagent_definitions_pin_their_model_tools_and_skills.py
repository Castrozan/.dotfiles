from instruction_surface_scanner import (
    REPO_ROOT,
    frontmatter_key_values,
    subagent_definition_files,
)

SKILL_TREE = REPO_ROOT / "agent-harness" / "agent-instructions" / "skills"
SUBAGENT_TREE = REPO_ROOT / "agents" / "subagents"


def subagent_frontmatter():
    return [
        (definition, frontmatter_key_values(definition.read_text()) or {})
        for definition in subagent_definition_files()
    ]


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
            if skill_name and not (SKILL_TREE / skill_name / "SKILL.md").is_file():
                unresolved.append(f"{label(definition)} -> {skill_name}")
    return unresolved


def test_every_subagent_name_matches_its_own_filename():
    mismatched = name_mismatches(subagent_frontmatter())
    assert not mismatched, (
        "a subagent registers under its frontmatter name, not its filename, so a "
        "typo silently creates an extra agent nobody routes to and leaves the one "
        "named by the file absent; capitalisation may differ because a definition "
        "overriding a built-in has to reproduce the built-in's own casing: "
        + ", ".join(mismatched)
    )


def test_every_subagent_pins_an_explicit_model():
    unpinned = definitions_without_a_model(subagent_frontmatter())
    assert not unpinned, (
        "a subagent with no model frontmatter inherits the session model, so the "
        "delegated tier silently runs whatever the lead is running: "
        + ", ".join(unpinned)
    )


def test_every_subagent_declares_a_tool_policy():
    unrestricted = definitions_without_a_tool_policy(subagent_frontmatter())
    assert not unrestricted, (
        "a subagent declaring neither tools nor disallowedTools inherits the full "
        "tool set, so a read-only role can edit and delete without the definition "
        "ever saying it may: " + ", ".join(unrestricted)
    )


def test_every_skill_a_subagent_binds_exists_on_disk():
    unresolved = unresolved_skill_bindings(subagent_frontmatter())
    assert not unresolved, (
        "these subagents bind skills that do not exist, so the agent loads nothing "
        "and improvises from ambient context while the definition still reads as "
        "though the method were attached: " + ", ".join(unresolved)
    )


def test_the_subagent_scan_covers_the_declared_roster():
    names = {keys.get("name") for _, keys in subagent_frontmatter()}
    assert {"software-engineer", "quality-assurance", "Explore"} <= names, (
        f"the roster the delivery process names is not what is on disk: {names}"
    )


def test_the_subagent_checks_reject_a_broken_definition():
    broken = [
        (
            SUBAGENT_TREE / "software-enginer.md",
            {"name": "software-engineer", "skills": "coding-typo"},
        )
    ]
    assert name_mismatches(broken)
    assert definitions_without_a_model(broken)
    assert definitions_without_a_tool_policy(broken)
    assert unresolved_skill_bindings(broken)
