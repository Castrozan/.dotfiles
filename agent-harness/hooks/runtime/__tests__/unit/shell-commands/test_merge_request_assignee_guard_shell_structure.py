import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hook_module_loader import import_hyphenated_hook_module

merge_request_assignee_guard_handler = import_hyphenated_hook_module(
    "merge_request_assignee_guard_handler"
)


def guard(command):
    return merge_request_assignee_guard_handler.handle(
        {"tool_name": "Bash", "tool_input": {"command": command}}
    )


def test_allows_a_rest_creation_naming_the_assignee_in_the_query_string():
    assert (
        guard(
            "curl -X POST --data-binary @/tmp/body.json "
            '"https://gitlab.example.com/api/v4/projects/1/merge_requests?assignee_id=7"'
        )
        is None
    )


@pytest.mark.parametrize(
    "command",
    [
        'jq -n \'{source_branch:"feature", title:"thing", assignee_id:683}\' '
        '| glab api -X POST "projects/1/merge_requests" --input - '
        '-H "Content-Type: application/json"',
        "cat > /tmp/body.json <<'EOF'\n"
        '{"source_branch": "feature", "title": "thing", "assignee_ids": [683]}\n'
        "EOF\n"
        "glab api -X POST projects/1/merge_requests --input /tmp/body.json",
    ],
)
def test_allows_a_rest_creation_whose_body_is_built_with_an_assignee(command):
    assert guard(command) is None, command


def test_denies_a_creation_that_follows_a_script_fed_to_another_interpreter():
    result = guard(
        "python3 - <<'EOF'\n"
        "text = '''it's (one) `quoted` body'''\n"
        "print(text)\n"
        "EOF\n"
        "git push -q -u origin feature; glab mr create --fill --yes 2>&1 | tail -1"
    )
    assert result is not None
    assert result.decision == "deny"


def test_allows_a_push_option_creation_because_gitlab_assigns_the_pusher():
    assert (
        guard(
            "git push -u origin feature -o merge_request.create "
            '-o merge_request.target=main -o merge_request.title="feat: thing"'
        )
        is None
    )


def test_reads_the_assignee_past_a_heredoc_description_on_continued_lines():
    creation = (
        "glab mr create \\\n"
        '  --title "feat: thing" \\\n'
        "  --description \"$(cat <<'EOF'\n"
        "It's one (1) change; nothing else.\n"
        "EOF\n"
        ')"{assignee} \\\n'
        "  --yes"
    )
    assert guard(creation.format(assignee=" --assignee @me")) is None
    assert guard(creation.format(assignee="")).decision == "deny"


def test_an_assignee_flag_written_inside_the_description_does_not_count():
    result = guard(
        "glab mr create --title thing --description \"$(cat <<'EOF'\n"
        "Reviewers should pass --assignee @me from now on.\n"
        "EOF\n"
        ')" --yes'
    )
    assert result is not None
    assert result.decision == "deny"


def test_an_assignee_flag_on_a_later_command_does_not_count():
    result = guard("glab mr create --fill --yes && git tag -a v1 -m v1")
    assert result is not None
    assert result.decision == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "URL=$(glab mr create --fill --yes)",
        'echo "opened $(gh pr create --fill)"',
        "echo `glab mr create --fill --yes`",
        "(cd /repo/project && glab mr create --fill --yes)",
        "if glab mr create --fill --yes; then echo opened; fi",
        "bash <<'EOF'\nglab mr create --fill --yes\nEOF",
    ],
)
def test_denies_a_creation_nested_in_shell_structure(command):
    result = guard(command)
    assert result is not None, command
    assert result.decision == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "glab mr create --help",
        "gh pr create -h",
        "glab mr list --assignee=@me",
        "glab mr view 12",
        "glab mr update 12 --title thing",
        "glab mr merge 12 --yes",
        "gh pr view 3 --json state",
        "gh pr list",
        "glab issue create --title 'mr create flow'",
        "glab api projects/1/merge_requests",
        'glab api "projects/1/merge_requests?state=opened"',
        "glab api -X GET projects/1/merge_requests -f state=opened",
        "glab api -X PUT projects/1/merge_requests/5 -f title=thing",
        "glab api -X POST projects/1/merge_requests/5/notes -f body=thing",
        "curl -G -d state=opened https://gitlab.example.com/api/v4/projects/1/merge_requests",
        "curl -sS https://gitlab.example.com/api/v4/projects/1/merge_requests",
    ],
)
def test_ignores_commands_that_open_no_merge_request(command):
    assert guard(command) is None, command


@pytest.mark.parametrize(
    "command",
    [
        'echo "glab mr create --fill"',
        "grep -rn 'glab mr create' agent-harness",
        'git commit -m "docs: say (glab mr create) needs an assignee"',
        "git commit -m 'docs: explain `gh pr create`'",
        "cat > /tmp/notes.md <<'EOF'\nglab mr create --fill --yes\nEOF",
        "# glab mr create --fill\ngit status --short",
    ],
)
def test_ignores_a_creation_that_is_only_mentioned(command):
    assert guard(command) is None, command


def test_a_sanctioned_override_lets_an_unassigned_creation_through():
    sentinel = merge_request_assignee_guard_handler.WITHOUT_ASSIGNEE_OVERRIDE_SENTINEL
    assert guard(f"{sentinel} gh pr create --fill") is None


def test_ignores_tools_other_than_bash():
    assert (
        merge_request_assignee_guard_handler.handle(
            {"tool_name": "Write", "tool_input": {"command": "glab mr create"}}
        )
        is None
    )


def test_the_denial_shows_the_fix_and_points_at_its_reference_file():
    result = guard("glab mr create --fill --yes")
    assert "'glab mr create'" in result.reason
    assert (
        merge_request_assignee_guard_handler.MERGE_REQUEST_ASSIGNEE_REFERENCE_FILE_PATH
        in result.reason
    )
    assert len(result.reason) <= 300
