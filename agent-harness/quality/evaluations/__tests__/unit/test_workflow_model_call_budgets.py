import json
import re

from instruction_surface_scanner import REPO_ROOT


DOTFILES_WORKFLOW_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "harnesses" / "claude-code" / "workflows"
)
CHANGE_REVIEW_WORKFLOW_PATH = DOTFILES_WORKFLOW_DIRECTORY / "dotfiles-change-review.js"
PAGE_COMPOSER_WORKFLOW_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "page-composer"
    / "compose-page.js"
)
RESEARCH_PULSE_WORKFLOW_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "research"
    / "research-pulse.workflow.js"
)
MAXIMUM_MODEL_CALLS_PER_ROUTINE_WORKFLOW = 2
MAXIMUM_RESEARCH_SOURCE_CALLS = 7
SUPPORTED_EFFORT_LEVELS = "low|medium|high|xhigh|max"


def routine_workflow_paths():
    return sorted(DOTFILES_WORKFLOW_DIRECTORY.glob("dotfiles-*.js")) + [
        PAGE_COMPOSER_WORKFLOW_PATH
    ]


def every_workflow_path():
    return routine_workflow_paths() + [RESEARCH_PULSE_WORKFLOW_PATH]


def model_call_count(source):
    return len(re.findall(r"\bagent\s*\(", source))


def test_routine_workflows_stay_within_their_model_call_budget():
    for workflow_path in routine_workflow_paths():
        source = workflow_path.read_text()
        assert model_call_count(source) <= MAXIMUM_MODEL_CALLS_PER_ROUTINE_WORKFLOW, (
            f"{workflow_path.name} declares {model_call_count(source)} agent call "
            f"sites; routine workflows may declare at most "
            f"{MAXIMUM_MODEL_CALLS_PER_ROUTINE_WORKFLOW}"
        )
        assert "parallel(" not in source, (
            f"{workflow_path.name} uses parallel fan-out instead of its fixed call budget"
        )
        assert "pipeline(" not in source, (
            f"{workflow_path.name} uses pipeline fan-out instead of its fixed call budget"
        )
        for dynamic_call_pattern in (
            "for (",
            "for await (",
            "while (",
            ".forEach(",
            "Promise.all(",
        ):
            assert dynamic_call_pattern not in source, (
                f"{workflow_path.name} uses {dynamic_call_pattern} around a routine "
                "workflow; keep model-call control flow visibly fixed"
            )
        first_map_position = source.find(".map(")
        last_model_call_position = source.rfind("agent(")
        assert (
            first_map_position == -1 or first_map_position > last_model_call_position
        ), f"{workflow_path.name} maps data before its final agent call"


def test_routine_workflows_pin_the_model_and_the_effort_of_every_call():
    for workflow_path in routine_workflow_paths():
        source = workflow_path.read_text()
        calls = model_call_count(source)
        pinned_models = len(re.findall(r'model: "(?:haiku|sonnet|opus)"', source))
        pinned_efforts = len(
            re.findall(rf'effort: "(?:{SUPPORTED_EFFORT_LEVELS})"', source)
        )
        assert pinned_models == calls, (
            f"{workflow_path.name} pins {pinned_models} models for {calls} calls; an "
            "unpinned call inherits the caller's model"
        )
        assert pinned_efforts == calls, (
            f"{workflow_path.name} pins {pinned_efforts} efforts for {calls} calls; an "
            "unpinned call inherits the caller's reasoning effort, so its cost and "
            "latency depend on whoever invoked the workflow"
        )


def test_no_workflow_claims_a_turn_ceiling_the_harness_does_not_enforce():
    for workflow_path in every_workflow_path():
        source = workflow_path.read_text()
        assert "maxTurns" not in source, (
            f"{workflow_path.name} declares maxTurns, which the workflow runner does "
            "not accept: it silently ignores the option and the call runs unbounded. "
            "Bound a call through its prompt and its pinned effort instead"
        )


def test_the_change_review_hands_its_verify_pass_the_patch_the_review_pass_wrote():
    source = CHANGE_REVIEW_WORKFLOW_PATH.read_text()
    assert '"patchPath"' in source, (
        "the review pass must return the patch it wrote so the verify pass reads the "
        "same change instead of rediscovering it one file at a time"
    )
    verify_prompt = source.split('phase("Verify")', 1)[1]
    assert "candidates.patchPath" in verify_prompt, (
        "the verify pass must be handed the review pass's patch path"
    )
    assert "candidates.repoRoot" in verify_prompt, (
        "the verify pass must be anchored at the repository root the review pass "
        "resolved, or it inspects a sibling checkout and reports defects that are "
        "not in this change"
    )


def test_the_change_review_accepts_its_arguments_as_a_json_string():
    source = CHANGE_REVIEW_WORKFLOW_PATH.read_text()
    assert "JSON.parse" in source, (
        "the runner can deliver args as a JSON string rather than an object, and "
        "reading .root off that string yields undefined, so the explicit checkout "
        "anchor silently disappears"
    )


def test_the_change_review_writes_a_patch_path_no_sibling_checkout_can_collide_with():
    source = CHANGE_REVIEW_WORKFLOW_PATH.read_text()
    assert "mktemp" in source, (
        "a patch path keyed on the commit alone collides between sibling checkouts "
        "sharing a HEAD, so one review overwrites the patch another is about to read"
    )
    assert re.search(r"mktemp \S*X(?![\w.])", source), (
        "the mktemp template must end in X characters: BSD mktemp on darwin leaves a "
        "template with a trailing suffix unexpanded and hands back the literal path, "
        "so every run would share one file"
    )


def test_the_documented_change_review_arguments_parse_as_json():
    documentation = (
        REPO_ROOT
        / "agent-harness"
        / "agent-instructions"
        / "project-context"
        / "dotfiles-agent-instructions.md"
    ).read_text()
    example = re.search(r"`(\{[^`]*\})`", documentation)
    assert example, "the mandated invocation must show how to pass the checkout root"
    parsed = json.loads(example.group(1).replace("<absolute checkout path>", "/x"))
    assert "root" in parsed, (
        "the documented example must carry the root key the workflow reads; the "
        "workflow parses a string argument with JSON.parse and silently drops the "
        "anchor when the example is not valid JSON"
    )


def test_the_change_review_names_the_checkout_it_found_clean():
    source = CHANGE_REVIEW_WORKFLOW_PATH.read_text()
    empty_branch = source.split("No diff to review", 1)[0].rsplit("if (", 1)[1]
    assert "repoRoot" in empty_branch, (
        "an empty result must name the checkout it inspected: the shell can start in "
        "a sibling checkout, and a bare 'no diff' reads as a clean tree when the pass "
        "reviewed the wrong repository"
    )


def test_the_explicit_research_fanout_pins_every_call_to_a_bounded_model():
    source = RESEARCH_PULSE_WORKFLOW_PATH.read_text()
    pinned_call_count = len(
        re.findall(
            rf'"(?:haiku|sonnet)",\s*"(?:{SUPPORTED_EFFORT_LEVELS})"',
            source,
        )
    )
    assert pinned_call_count == model_call_count(source)
    assert "  model," in source
    assert "  effort," in source
    sources = source.split("const SOURCES = [", 1)[1].split("];", 1)[0]
    source_call_count = len(re.findall(r'^    key: "', sources, re.MULTILINE))
    assert source_call_count <= MAXIMUM_RESEARCH_SOURCE_CALLS
