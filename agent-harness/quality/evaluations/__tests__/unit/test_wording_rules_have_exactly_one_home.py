import re

from instruction_surface_scanner import REPO_ROOT, every_linted_markdown_file

CORE_CODING_AUTHORITY = frozenset(
    {"agent-harness/agent-instructions/core-rules/core.md"}
)
HUMANIZE_SKILL = frozenset(
    {"agent-harness/agent-instructions/skills/humanize/SKILL.md"}
)
INTERACTIVE_INSTRUCTIONS = frozenset(
    {"agent-harness/agent-instructions/skills/humanize/interactive-communication.md"}
)
MIGRATED_CODING_SURFACES = frozenset(
    {
        "agent-harness/agent-instructions/skills/agent-harness/SKILL.md",
        "agent-harness/agent-instructions/skills/architecture/SKILL.md",
        "agent-harness/agent-instructions/skills/coding/SKILL.md",
        "agent-harness/agent-instructions/skills/coding/testing.md",
        "agent-harness/agent-instructions/skills/docs/SKILL.md",
        "agent-harness/agent-instructions/skills/nix/expert.md",
    }
)
NO_COMMENTS_RULE_PHRASE = (
    "add no comments, docstrings, section banners, commented-out code, TODO notes, "
    "or FIXME notes"
)
NO_COMMENTS_RULE_ITEMS = (
    "comments",
    "docstrings",
    "section banners",
    "commented-out code",
    "todo notes",
    "fixme notes",
)
NO_COMMENTS_RULE_RESTATEMENTS = (
    "add no comments",
    "never code comments",
)

SINGLE_HOME_RULE_PHRASES = {
    "Give a direct link": HUMANIZE_SKILL,
    NO_COMMENTS_RULE_PHRASE: CORE_CODING_AUTHORITY,
}


def normalized_text(path: str) -> str:
    return re.sub(r"\s+", " ", (REPO_ROOT / path).read_text(encoding="utf-8"))


def surfaces_stating(phrase: str) -> set[str]:
    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
    return {
        str(path.relative_to(REPO_ROOT))
        for path in every_linted_markdown_file()
        if pattern.search(re.sub(r"\s+", " ", path.read_text(encoding="utf-8")))
    }


def test_no_wording_rule_is_stated_outside_its_single_home():
    trespassers = {
        phrase: sorted(surfaces_stating(phrase) - allowed_surfaces)
        for phrase, allowed_surfaces in SINGLE_HOME_RULE_PHRASES.items()
        if surfaces_stating(phrase) - allowed_surfaces
    }
    assert not trespassers, (
        "a wording rule stated in two active instruction surfaces drifts when one is "
        "edited; point at the canonical authority instead of restating it "
        f"(phrase -> surfaces that restate it): {trespassers}"
    )


def test_every_guarded_phrase_is_actually_stated_somewhere():
    unstated = [
        phrase
        for phrase, allowed_surfaces in SINGLE_HOME_RULE_PHRASES.items()
        if not set(surfaces_stating(phrase)) & allowed_surfaces
    ]
    assert not unstated, (
        "these phrases are guarded as single-home rules but no longer appear in the "
        "surface that owns them, so the guard is inspecting nothing and would pass "
        f"even if the rule were restated everywhere: {unstated}"
    )


def test_migrated_skills_point_to_core_coding_authority():
    missing_routes = sorted(
        path
        for path in MIGRATED_CODING_SURFACES
        if "core" not in normalized_text(path).lower()
        or "<coding>" not in normalized_text(path).lower()
    )
    assert not missing_routes, (
        "migrated skills may add bounded procedure only when they point to core "
        f"<coding> as the persistent authority: {missing_routes}"
    )


def test_the_full_no_comments_rule_does_not_return_to_migrated_skills():
    duplicate_authorities = sorted(
        path
        for path in MIGRATED_CODING_SURFACES
        if all(item in normalized_text(path).lower() for item in NO_COMMENTS_RULE_ITEMS)
    )
    assert not duplicate_authorities, (
        "the full no-comments rule belongs only in core <coding>; migrated skills must "
        f"point to it instead of recreating a second authority: {duplicate_authorities}"
    )


def test_migrated_skills_do_not_restate_the_no_comments_default():
    duplicate_authorities = {
        path: [
            phrase
            for phrase in NO_COMMENTS_RULE_RESTATEMENTS
            if phrase in normalized_text(path).lower()
        ]
        for path in MIGRATED_CODING_SURFACES
        if any(
            phrase in normalized_text(path).lower()
            for phrase in NO_COMMENTS_RULE_RESTATEMENTS
        )
    }
    assert not duplicate_authorities, (
        "core <coding> owns the no-comments default; migrated skills must point to it "
        f"instead of paraphrasing it: {duplicate_authorities}"
    )
