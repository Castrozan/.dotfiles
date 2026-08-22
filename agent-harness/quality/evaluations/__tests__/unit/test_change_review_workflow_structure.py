import json
import re

from instruction_surface_scanner import REPO_ROOT


CHANGE_REVIEW_WORKFLOW_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "claude-code"
    / "workflows"
    / "dotfiles-change-review.js"
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


def test_the_change_review_reads_the_commits_rather_than_the_shared_working_tree():
    source = CHANGE_REVIEW_WORKFLOW_PATH.read_text()
    assert 'diff "$base..HEAD"' in source, (
        "several agents commit into this one checkout, so diffing the base against the "
        "working tree hands the review whatever a peer left uncommitted and reports "
        "defects that belong to somebody else's change"
    )
    assert 'diff --stat "$base..HEAD"' in source, (
        "the diffstat names the files the review reports, so it must cover the same "
        "range as the patch or the two disagree about what was reviewed"
    )


def test_the_change_review_names_the_checkout_it_found_clean():
    source = CHANGE_REVIEW_WORKFLOW_PATH.read_text()
    empty_branch = source.split("No diff to review", 1)[0].rsplit("if (", 1)[1]
    assert "repoRoot" in empty_branch, (
        "an empty result must name the checkout it inspected: the shell can start in "
        "a sibling checkout, and a bare 'no diff' reads as a clean tree when the pass "
        "reviewed the wrong repository"
    )


def test_the_change_review_never_calls_an_untracked_only_change_a_clean_tree():
    source = CHANGE_REVIEW_WORKFLOW_PATH.read_text()
    assert '"untrackedFiles"' in source, (
        "the review pass must return the untracked paths beside the diffstat ones, "
        "or nothing downstream can tell an untracked-only change from an empty tree"
    )
    empty_branch = source.split("No diff to review", 1)[0].rsplit("if (", 1)[1]
    assert "untrackedFiles" in empty_branch, (
        "a change made only of files git does not track yet reaches the clean-tree "
        "branch whenever the guard reads the diffstat alone, so the workflow reports "
        "a clean tree for a change it never reviewed"
    )


def test_the_change_review_hands_its_verify_pass_the_files_no_patch_holds():
    source = CHANGE_REVIEW_WORKFLOW_PATH.read_text()
    verify_prompt = source.split('phase("Verify")', 1)[1]
    assert "untrackedFiles" in verify_prompt, (
        "git diff never contains a file git is not tracking, so a verify pass handed "
        "the patch alone refutes every finding in a new file for lack of evidence"
    )
