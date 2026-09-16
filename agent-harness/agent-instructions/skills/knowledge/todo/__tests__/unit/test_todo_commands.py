import json
from unittest.mock import Mock

import pytest


def invoke(modules, arguments):
    parsed = modules.todo.build_parser().parse_args(arguments)
    parsed.handler(parsed, "test-token")


def test_add_preserves_all_requested_fields(todo_modules, monkeypatch, capsys):
    request = Mock(return_value={"id": "42", "content": "Ship café"})
    monkeypatch.setattr(todo_modules.commands, "send_request", request)
    monkeypatch.setattr(
        todo_modules.commands, "resolve_project_id", Mock(return_value="project")
    )
    invoke(
        todo_modules,
        [
            "add",
            "Ship café",
            "--due",
            "tomorrow",
            "--priority",
            "4",
            "--label",
            "work",
            "--label",
            "release",
            "--description",
            "notes",
            "--project",
            "Work",
            "--json",
        ],
    )
    request.assert_called_once_with(
        "POST",
        "/tasks",
        "test-token",
        body={
            "content": "Ship café",
            "due_string": "tomorrow",
            "priority": 4,
            "labels": ["work", "release"],
            "description": "notes",
            "project_id": "project",
        },
    )
    assert json.loads(capsys.readouterr().out) == {"id": "42", "content": "Ship café"}


def test_update_rejects_empty_changes_and_allows_clearing_description(
    todo_modules, monkeypatch, capsys
):
    request = Mock(return_value=None)
    monkeypatch.setattr(todo_modules.commands, "send_request", request)
    with pytest.raises(SystemExit, match="at least one field"):
        invoke(todo_modules, ["update", "42"])
    request.assert_not_called()
    invoke(todo_modules, ["update", "42", "--description", "", "--json"])
    request.assert_called_once_with(
        "POST", "/tasks/42", "test-token", body={"description": ""}
    )
    assert json.loads(capsys.readouterr().out) == {"id": "42"}
    invoke(
        todo_modules,
        [
            "update",
            "42",
            "--content",
            "Changed",
            "--due",
            "today",
            "--priority",
            "2",
            "--label",
            "work",
        ],
    )
    assert request.call_args.kwargs["body"] == {
        "content": "Changed",
        "due_string": "today",
        "priority": 2,
        "labels": ["work"],
    }
    assert capsys.readouterr().out == "updated 42\n"


@pytest.mark.parametrize(
    "command,method,path,message",
    [
        ("done", "POST", "/tasks/42/close", "completed"),
        ("reopen", "POST", "/tasks/42/reopen", "reopened"),
        ("delete", "DELETE", "/tasks/42", "deleted"),
    ],
)
def test_task_lifecycle_requests(
    todo_modules, monkeypatch, capsys, command, method, path, message
):
    request = Mock()
    monkeypatch.setattr(todo_modules.commands, "send_request", request)
    invoke(todo_modules, [command, "42"])
    request.assert_called_once_with(method, path, "test-token")
    assert capsys.readouterr().out == f"{message} 42\n"


def test_task_listing_filters_and_rendering(todo_modules, monkeypatch, capsys):
    task = {
        "id": "42",
        "content": "Ship",
        "due": {"date": "2026-09-17"},
        "labels": ["work"],
        "priority": 4,
    }
    fetch = Mock(return_value=[task])
    monkeypatch.setattr(todo_modules.commands, "fetch_paginated", fetch)
    invoke(todo_modules, ["list", "--filter", "today"])
    fetch.assert_called_once_with(
        "/tasks/filter", "test-token", query={"query": "today"}
    )
    assert capsys.readouterr().out == "42  Ship  [due 2026-09-17]  @work  p1\n"
    invoke(todo_modules, ["list", "--json"])
    assert json.loads(capsys.readouterr().out) == [task]
    fetch.return_value = []
    invoke(todo_modules, ["list"])
    assert capsys.readouterr().out == "(no tasks)\n"
    assert todo_modules.render.format_task_line({}) == "?  "
    assert (
        todo_modules.render.format_task_line({"due": {"string": "tomorrow"}})
        == "?    [due tomorrow]"
    )


def test_digest_and_projects_offer_json_and_human_output(
    todo_modules, monkeypatch, capsys
):
    fetch = Mock(side_effect=[[{"id": "1", "content": "Late"}], [], []] * 2)
    monkeypatch.setattr(todo_modules.commands, "fetch_paginated", fetch)
    invoke(todo_modules, ["digest", "--json"])
    assert json.loads(capsys.readouterr().out) == {
        "overdue": [{"id": "1", "content": "Late"}],
        "today": [],
        "someday": [],
    }
    invoke(todo_modules, ["digest"])
    assert (
        capsys.readouterr().out
        == "Overdue (1)\n  1  Late\n\nToday (0)\n\nSomeday (0)\n\n"
    )
    assert [call.kwargs["query"]["query"] for call in fetch.call_args_list[:3]] == [
        "overdue",
        "today",
        "no date",
    ]
    fetch.side_effect = None
    fetch.return_value = [{"id": "42", "name": "Work"}]
    invoke(todo_modules, ["projects"])
    assert capsys.readouterr().out == "42  Work\n"
    invoke(todo_modules, ["projects", "--json"])
    assert json.loads(capsys.readouterr().out) == fetch.return_value
