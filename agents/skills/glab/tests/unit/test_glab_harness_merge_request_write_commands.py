import json
from unittest.mock import MagicMock, patch

import pytest


class TestCommandMergeRequestView:
    @patch("urllib.request.urlopen")
    def test_prints_merge_request_details(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            {
                "iid": 88,
                "title": "Tiered permissions",
                "state": "opened",
                "source_branch": "feature/tiered",
                "target_branch": "develop",
                "author": {"username": "lucas"},
                "assignees": [{"username": "lucas"}],
                "reviewers": [{"username": "brian"}],
                "has_conflicts": False,
                "detailed_merge_status": "mergeable",
                "web_url": "https://git.coates.io/mr/88",
                "description": "Test description",
            }
        )
        args = MagicMock(iid=88)
        glab_harness_module.command_merge_request_view(
            args, "fake-token", "test/project", "git.coates.io"
        )
        output = capsys.readouterr().out
        assert "!88" in output
        assert "Tiered permissions" in output
        assert "lucas" in output
        assert "brian" in output


class TestCommandMergeRequestCreate:
    @patch("urllib.request.urlopen")
    def test_creates_merge_request_with_required_fields(
        self, mock_urlopen, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            {"iid": 42, "title": "Test", "web_url": "https://example.com/mr/42"}
        )
        args = MagicMock(
            source="feature/test",
            target="develop",
            title="Test",
            description_file=None,
            assignee=None,
            reviewer=None,
            remove_source_branch=False,
        )
        glab_harness_module.command_merge_request_create(
            args, "fake-token", "test/project", "git.coates.io"
        )
        sent_request = mock_urlopen.call_args[0][0]
        sent_body = json.loads(sent_request.data)
        assert sent_body["source_branch"] == "feature/test"
        assert sent_body["target_branch"] == "develop"
        assert sent_body["title"] == "Test"

    @patch("urllib.request.urlopen")
    def test_reads_description_from_file(
        self, mock_urlopen, tmp_path, glab_harness_module, make_mock_http_response
    ):
        description_file = tmp_path / "description.md"
        description_file.write_text(
            "## What\n- Feature with `special` chars & markdown\n"
        )
        mock_urlopen.return_value = make_mock_http_response(
            {"iid": 43, "title": "With desc", "web_url": "https://example.com/mr/43"}
        )
        args = MagicMock(
            source="feature/test",
            target="develop",
            title="With desc",
            description_file=str(description_file),
            assignee=None,
            reviewer=None,
            remove_source_branch=False,
        )
        glab_harness_module.command_merge_request_create(
            args, "fake-token", "test/project", "git.coates.io"
        )
        sent_body = json.loads(mock_urlopen.call_args[0][0].data)
        assert "special" in sent_body["description"]
        assert "&" in sent_body["description"]


class TestCommandMergeRequestUpdate:
    @patch("urllib.request.urlopen")
    def test_updates_title(
        self, mock_urlopen, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            {"iid": 88, "title": "New title", "web_url": "https://example.com/mr/88"}
        )
        args = MagicMock(
            iid=88,
            title="New title",
            description_file=None,
            assignee=None,
            reviewer=None,
        )
        glab_harness_module.command_merge_request_update(
            args, "fake-token", "test/project", "git.coates.io"
        )
        sent_body = json.loads(mock_urlopen.call_args[0][0].data)
        assert sent_body["title"] == "New title"

    @patch("urllib.request.urlopen")
    def test_updates_description_from_file(
        self, mock_urlopen, tmp_path, glab_harness_module, make_mock_http_response
    ):
        description_file = tmp_path / "desc.md"
        description_file.write_text("Updated description with @mentions and `code`")
        mock_urlopen.return_value = make_mock_http_response(
            {"iid": 88, "title": "Same", "web_url": "https://example.com/mr/88"}
        )
        args = MagicMock(
            iid=88,
            title=None,
            description_file=str(description_file),
            assignee=None,
            reviewer=None,
        )
        glab_harness_module.command_merge_request_update(
            args, "fake-token", "test/project", "git.coates.io"
        )
        sent_body = json.loads(mock_urlopen.call_args[0][0].data)
        assert "@mentions" in sent_body["description"]

    def test_exits_when_no_fields_provided(self, glab_harness_module):
        args = MagicMock(
            iid=88, title=None, description_file=None, assignee=None, reviewer=None
        )
        with pytest.raises(SystemExit):
            glab_harness_module.command_merge_request_update(
                args, "fake-token", "test/project", "git.coates.io"
            )
