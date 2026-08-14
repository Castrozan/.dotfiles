import re

from instruction_surface_scanner import REPO_ROOT, every_linted_markdown_file

GENERATED_RULE_SURFACES = frozenset(
    {
        "agent-harness/agent-instructions/core-rules/communication/interactive-hook-communication.md",
        "agent-harness/agent-instructions/core-rules/communication/interactive-human-communication.md",
        "agent-harness/agent-instructions/skills/humanize/enforced-wording-rules.md",
    }
)

SINGLE_HOME_RULE_PHRASES = {
    "em dash": GENERATED_RULE_SURFACES,
    "en dash": GENERATED_RULE_SURFACES,
    "sycophancy phrase": GENERATED_RULE_SURFACES,
    "numbered list": GENERATED_RULE_SURFACES,
    "prose words": GENERATED_RULE_SURFACES,
    "prose lines": GENERATED_RULE_SURFACES,
}


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
        "a wording rule stated in two surfaces drifts the moment one is edited, which is "
        "why the rule catalog in agent-harness/hooks/runtime/common/human_facing_reply renders the only "
        "copies; point at the generated surface instead of restating it "
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
