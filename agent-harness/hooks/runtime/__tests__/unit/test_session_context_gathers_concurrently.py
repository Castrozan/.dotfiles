import time

import session_context_git_status
import session_context_handler
import session_context_project_context

GIT_STATUS_PORCELAIN_V2 = (
    "# branch.oid 1234567890abcdef\n"
    "# branch.head main\n"
    "# branch.upstream origin/main\n"
    "# branch.ab +3 -1\n"
    "1 .M N... 100644 100644 100644 aaa bbb tracked_modified.py\n"
    "1 M. N... 100644 100644 100644 ccc ddd staged.py\n"
    "? untracked.py\n"
)


def record_invocations(monkeypatch, module, responses, delay_seconds=0.0):
    invocations = []

    def fake_run_cmd(args, timeout=5):
        invocations.append(tuple(args))
        if delay_seconds:
            time.sleep(delay_seconds)
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
        delay_seconds=0.15,
    )
    started_at = time.perf_counter()
    session_context_project_context.check_project_context()
    elapsed_seconds = time.perf_counter() - started_at
    assert elapsed_seconds < 0.28, (
        "the worktree listing and the WIP-commit search do not depend on each other, "
        f"so running them sequentially doubles the wall time: {elapsed_seconds:.3f}s"
    )


def test_handler_gathers_its_sections_concurrently(monkeypatch):
    for section_name in (
        "get_git_status",
        "check_environment",
        "detect_hyprland_workspace_context",
        "check_project_context",
        "get_system_info",
    ):
        monkeypatch.setattr(
            session_context_handler,
            section_name,
            lambda *_: time.sleep(0.12) or {},
        )
    started_at = time.perf_counter()
    session_context_handler.handle({"hook_event_name": "SessionStart"})
    elapsed_seconds = time.perf_counter() - started_at
    assert elapsed_seconds < 0.35, (
        "the five context gatherers are independent and every one of them is blocked "
        f"on a subprocess, so they must not run one after another: {elapsed_seconds:.3f}s"
    )
