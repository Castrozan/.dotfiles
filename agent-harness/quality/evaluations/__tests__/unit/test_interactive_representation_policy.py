import re

from instruction_surface_scanner import REPO_ROOT

CANONICAL_HUMAN_COMMUNICATION_POLICY_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "humanize"
    / "SKILL.md"
)
INTERACTIVE_COMMUNICATION_POLICY_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "humanize"
    / "references"
    / "interactive-communication.md"
)


def representation_selection_policy() -> str:
    preferences = CANONICAL_HUMAN_COMMUNICATION_POLICY_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"<representation_selection>(.*?)</representation_selection>",
        preferences,
        re.DOTALL,
    )
    assert match, "interactive sessions need one always-loaded representation policy"
    return re.sub(r"\s+", " ", match.group(1)).strip().lower()


def representation_rendering_policy() -> str:
    preferences = CANONICAL_HUMAN_COMMUNICATION_POLICY_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"<representation_rendering>(.*?)</representation_rendering>",
        preferences,
        re.DOTALL,
    )
    assert match, "Humanize needs one representation-rendering policy"
    return re.sub(r"\s+", " ", match.group(1)).strip().lower()


def test_representation_policy_maps_reader_needs_to_the_smallest_useful_form():
    policy = representation_selection_policy()
    required_mappings = {
        "ownership": "tree",
        "ordering or failure": "sequence",
        "choices": "table",
        "behavior": "state model",
        "change": "focused diff",
        "one answer or action": "prose",
    }

    assert "smallest useful" in policy
    missing = {
        reader_need: representation
        for reader_need, representation in required_mappings.items()
        if reader_need not in policy or representation not in policy
    }
    assert not missing, (
        f"representation policy is missing reader-need mappings: {missing}"
    )
    for required_behavior in (
        "diagram",
        "well-spaced",
        "repeated-field",
        "linear prose",
    ):
        assert required_behavior in policy
    assert "pseudocode" in representation_rendering_policy()


def test_interactive_contract_explicitly_allows_the_selected_representation():
    policy = INTERACTIVE_COMMUNICATION_POLICY_PATH.read_text(encoding="utf-8").lower()
    assert "representation_selection" in policy
    assert "smallest useful form" in policy
    assert "no bullet" not in policy
