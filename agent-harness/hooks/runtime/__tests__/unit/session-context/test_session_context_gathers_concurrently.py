import threading

import session_context_git_status
import session_context_handler
import session_context_project_context
from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS

GIT_STATUS_PORCELAIN_V2 = (
    "# branch.oid 1234567890abcdef\n"
    "# branch.head main\n"
    "# branch.upstream origin/main\n"
    "# branch.ab +3 -1\n"
    "1 .M N... 100644 100644 100644 aaa bbb tracked_modified.py\n"
    "1 M. N... 100644 100644 100644 ccc ddd staged.py\n"
    "? untracked.py\n"
)


def record_invocations(monkeypatch, module, responses, overlap_barrier=None):
    invocations = []

    def fake_run_cmd(args, timeout=5):
        invocations.append(tuple(args))
        if overlap_barrier:
            overlap_barrier.wait()
        for prefix, response in responses.items():
            if tuple(args)[: len(prefix)] == prefix:
                return response
        return 1, ""

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)
    return invocations


def git_status_responses():
    return {
        ("git", "rev-parse"): (0, "true"),
        ("git", "branch"): (0, "main"),
        ("git", "rev-list"): (0, "1\t3"),
        ("git", "status"): (0, GIT_STATUS_PORCELAIN_V2),
        ("git", "log"): (0, "abc1234 a commit subject"),
    }


def test_git_status_issues_at_most_two_git_invocations(monkeypatch):
    invocations = record_invocations(
        monkeypatch, session_context_git_status, git_status_responses()
    )
    session_context_git_status.get_git_status()
    assert len(invocations) <= 2, (
        "SessionStart pays one process spawn per git invocation and this ran five of "
        "them sequentially; git status --porcelain=v2 --branch already carries the "
        f"branch, the ahead/behind counts and the file states in one call: {invocations}"
    )


def test_git_status_parses_branch_counts_and_last_commit(monkeypatch):
    record_invocations(monkeypatch, session_context_git_status, git_status_responses())
    status = session_context_git_status.get_git_status()
    assert status["is_repo"] is True
    assert status["branch"] == "main"
    assert status["ahead"] == 3
    assert status["behind"] == 1
    assert status["uncommitted"] == 3
    assert status["staged"] == 1
    assert status["untracked"] == 1
    assert status["last_commit"] == "abc1234 a commit subject"


def test_git_status_reports_not_a_repository_without_a_branch_header(monkeypatch):
    record_invocations(monkeypatch, session_context_git_status, {})
    assert session_context_git_status.get_git_status() == {"is_repo": False}


def test_project_context_runs_its_git_probes_concurrently(monkeypatch):
    record_invocations(
        monkeypatch,
        session_context_project_context,
        {("git", "worktree"): (0, "worktree /a\nworktree /b\n")},
        overlap_barrier=threading.Barrier(2, timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS),
    )
    session_context_project_context.check_project_context()


def test_handler_gathers_its_sections_concurrently(monkeypatch):
    section_names = (
        "get_git_status",
        "check_environment",
        "detect_hyprland_workspace_context",
        "check_project_context",
        "get_system_info",
    )
    all_sections_running = threading.Barrier(
        len(section_names), timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS
    )

    def section_that_waits_for_every_other_section(*_):
        all_sections_running.wait()
        return {}

    for section_name in section_names:
        monkeypatch.setattr(
            session_context_handler,
            section_name,
            section_that_waits_for_every_other_section,
        )
    session_context_handler.handle({"hook_event_name": "SessionStart"})
