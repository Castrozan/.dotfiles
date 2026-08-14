import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
REPLY_RULE_MODULE_DIRECTORY = next(HOOKS_ROOT.rglob("reply_rule_catalog.py")).parent
if str(REPLY_RULE_MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(REPLY_RULE_MODULE_DIRECTORY))

from reply_rule_catalog import HUMAN_FACING_REPLY_RULES  # noqa: E402
from reply_rule_rendering import (  # noqa: E402
    rendered_bounce_guidance,
    rendered_every_channel_wording_rules_markdown,
    rendered_interactive_hook_communication_markdown,
    rendered_interactive_human_communication_markdown as render_full_surface,
)
from reply_template_limits import (  # noqa: E402
    EVERY_HUMAN_FACING_CHANNEL_SCOPE,
    LIVE_KEYBOARD_REPLY_SCOPE,
)

REPOSITORY_ROOT = HOOKS_ROOT.parents[2]
HUMANIZE_SKILL_PATH = (
    REPOSITORY_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "humanize"
    / "SKILL.md"
)


def human_readable_output_policy_markdown() -> str:
    skill_text = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8")
    opening_tag = "<human-readable-output>"
    closing_tag = "</human-readable-output>"
    opening_index = skill_text.index(opening_tag)
    closing_index = skill_text.index(closing_tag) + len(closing_tag)
    return skill_text[opening_index:closing_index] + "\n"


def rendered_interactive_human_communication_markdown() -> str:
    return render_full_surface(human_readable_output_policy_markdown())


GENERATED_SURFACES = (
    (
        REPOSITORY_ROOT
        / "agent-harness"
        / "agent-instructions"
        / "core-rules"
        / "communication"
        / "interactive-human-communication.md",
        rendered_interactive_human_communication_markdown,
    ),
    (
        REPOSITORY_ROOT
        / "agent-harness"
        / "agent-instructions"
        / "core-rules"
        / "communication"
        / "interactive-hook-communication.md",
        rendered_interactive_hook_communication_markdown,
    ),
    (
        REPOSITORY_ROOT
        / "agent-harness"
        / "agent-instructions"
        / "skills"
        / "humanize"
        / "enforced-wording-rules.md",
        rendered_every_channel_wording_rules_markdown,
    ),
)


def test_every_rule_carries_an_instruction_sentence_for_the_rendered_surfaces():
    without_sentence = [
        rule.name
        for rule in HUMAN_FACING_REPLY_RULES
        if not rule.instruction_sentence.strip()
    ]
    assert not without_sentence, (
        "a rule enforced by regex but never stated to the model is the drift this "
        f"catalog exists to prevent: {without_sentence}"
    )


def test_the_bounce_text_carries_the_violations_and_the_template():
    bounce = rendered_bounce_guidance(["contains an em dash"])
    assert "contains an em dash" in bounce
    assert "**Done:**" in bounce


def test_every_committed_generated_surface_matches_the_catalog():
    stale = [
        str(surface_path.relative_to(REPOSITORY_ROOT))
        for surface_path, render in GENERATED_SURFACES
        if surface_path.read_text(encoding="utf-8") != render()
    ]
    assert not stale, (
        "these surfaces are generated; run "
        "agent-harness/agent-instructions/core-rules/communication/"
        "render-human-communication-markdown.py after editing the policy or rule "
        f"catalog so the deployed instruction text matches its sources: {stale}"
    )


def test_every_rule_declares_the_channels_it_binds():
    known_scopes = {EVERY_HUMAN_FACING_CHANNEL_SCOPE, LIVE_KEYBOARD_REPLY_SCOPE}
    unscoped = [
        rule.name
        for rule in HUMAN_FACING_REPLY_RULES
        if rule.applies_to not in known_scopes
    ]
    assert not unscoped, (
        "a rule with no channel scope reaches neither the humanize chapter nor the "
        f"reply surface, so it would be enforced without ever being stated: {unscoped}"
    )
