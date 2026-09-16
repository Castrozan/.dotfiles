import io
import json
import urllib.error
from unittest.mock import Mock

import pytest


def test_token_precedence_and_missing_credentials(todo_modules, monkeypatch, tmp_path):
    token_file = tmp_path / "token"
    monkeypatch.setattr(todo_modules.api, "TOKEN_FILE", str(token_file))
    monkeypatch.delenv("TODOIST_API_TOKEN", raising=False)
    with pytest.raises(SystemExit, match="No Todoist token"):
        todo_modules.api.resolve_api_token()
    token_file.write_text("file-token\n")
    assert todo_modules.api.resolve_api_token() == "file-token"
    monkeypatch.setenv("TODOIST_API_TOKEN", " environment-token ")
    assert todo_modules.api.resolve_api_token() == "environment-token"


@pytest.mark.parametrize(
    "payload,expected", [(b'{"id":"12"}', {"id": "12"}), (b"", None)]
)
def test_http_payload_headers_and_empty_response(
    todo_modules, monkeypatch, payload, expected
):
    opened = []

    def open_request(request):
        opened.append(request)
        return io.BytesIO(payload)

    monkeypatch.setattr(todo_modules.api.urllib.request, "urlopen", open_request)
    assert (
        todo_modules.api.send_request(
            "POST",
            "/tasks",
            "test-token",
            query={"query": "today | overdue"},
            body={"content": "café"},
        )
        == expected
    )
    request = opened[0]
    assert (
        request.full_url
        == "https://api.todoist.com/api/v1/tasks?query=today+%7C+overdue"
    )
    assert request.method == "POST"
    assert request.get_header("Authorization") == "Bearer test-token"
    assert request.get_header("Content-type") == "application/json"
    assert json.loads(request.data) == {"content": "café"}
    todo_modules.api.send_request("GET", "/projects", "test-token")
    assert opened[1].data is None
    assert opened[1].get_header("Content-type") is None


@pytest.mark.parametrize(
    "error,message",
    [
        (
            urllib.error.HTTPError(
                "https://example.test", 429, "limited", {}, io.BytesIO(b"retry later")
            ),
            "Todoist API error 429: retry later",
        ),
        (urllib.error.URLError("offline"), "Todoist request failed: offline"),
    ],
)
def test_transport_failures_retain_actionable_details(
    todo_modules, monkeypatch, error, message
):
    monkeypatch.setattr(
        todo_modules.api.urllib.request, "urlopen", Mock(side_effect=error)
    )
    with pytest.raises(SystemExit, match=message):
        todo_modules.api.send_request("GET", "/tasks", "test-token")


def test_pagination_retains_query_and_resolves_project(todo_modules, monkeypatch):
    request = Mock(
        side_effect=[
            {"results": [{"id": "1"}], "next_cursor": "next"},
            {"results": [{"id": "2"}]},
        ]
    )
    monkeypatch.setattr(todo_modules.api, "send_request", request)
    query = {"query": "today"}
    assert todo_modules.api.fetch_paginated("/tasks/filter", "token", query) == [
        {"id": "1"},
        {"id": "2"},
    ]
    assert query == {"query": "today"}
    assert request.call_args_list[1].kwargs == {
        "query": {"query": "today", "cursor": "next"}
    }
    projects = Mock(return_value=[{"id": "42", "name": "Work"}])
    monkeypatch.setattr(todo_modules.api, "fetch_paginated", projects)
    assert todo_modules.api.resolve_project_id("wOrK", "token") == "42"
    assert todo_modules.api.resolve_project_id("42", "token") == "42"
    with pytest.raises(SystemExit, match="Project not found: missing"):
        todo_modules.api.resolve_project_id("missing", "token")
