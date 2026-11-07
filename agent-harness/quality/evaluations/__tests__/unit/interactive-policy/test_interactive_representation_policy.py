import re

from instructions.instruction_surface_scanner import REPO_ROOT

CANONICAL_HUMAN_COMMUNICATION_POLICY_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "writing"
    / "humanize"
    / "SKILL.md"
)


def representation_selection_policy() -> str:
    preferences = CANONICAL_HUMAN_COMMUNICATION_POLICY_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"### Representation selection\n(.*?)(?=\n### |\Z)",
        preferences,
        re.DOTALL,
    )
    assert match, "humanize needs one representation selection policy"
    return re.sub(r"\s+", " ", match.group(1)).strip().lower()


def test_representation_policy_maps_reader_needs_to_the_smallest_useful_form():
    policy = representation_selection_policy()
    required_mappings = {
        "ownership": "tree",
        "failure paths": "sequences",
        "comparisons": "tables",
        "transitions": "state models",
        "exact edits": "diffs",
        "linear answer": "prose",
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
        "material actors",
        "relationships",
        "without repeating",
        "table rows",
    ):
        assert required_behavior in policy
