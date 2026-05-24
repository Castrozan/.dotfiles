import json
from unittest.mock import MagicMock, patch


class TestCommandMergeRequestDiscussions:
    @patch("urllib.request.urlopen")
    def test_prints_inline_code_comment_with_file_and_line(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            [
                {
                    "notes": [
                        {
                            "system": False,
                            "author": {
                                "name": "Vishwa Shah",
                                "username": "Vishwa.Shah",
                            },
                            "body": "seems like username is missing here",
                            "position": {
                                "new_path": "backend/services/users.service.ts",
                                "new_line": 55,
                            },
                        }
                    ]
                }
            ]
        )
        args = MagicMock(iid=87)
        glab_harness_module.command_merge_request_discussions(
            args, "fake-token", "test/project", "git.coates.io"
        )
        output = capsys.readouterr().out
        assert "Vishwa Shah" in output
        assert "users.service.ts:55" in output
        assert "username is missing" in output

    @patch("urllib.request.urlopen")
    def test_prints_general_comment_without_position(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            [
                {
                    "notes": [
                        {
                            "system": False,
                            "author": {"name": "Brian", "username": "Brian.A"},
                            "body": "LGTM",
                        }
                    ]
                }
            ]
        )
        args = MagicMock(iid=87)
        glab_harness_module.command_merge_request_discussions(
            args, "fake-token", "test/project", "git.coates.io"
        )
        output = capsys.readouterr().out
        assert "Brian" in output
        assert "LGTM" in output

    @patch("urllib.request.urlopen")
    def test_skips_system_notes(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            [
                {
                    "notes": [
                        {
                            "system": True,
                            "author": {"name": "System", "username": "system"},
                            "body": "merged",
                        }
                    ]
                }
            ]
        )
        args = MagicMock(iid=87)
        glab_harness_module.command_merge_request_discussions(
            args, "fake-token", "test/project", "git.coates.io"
        )
        output = capsys.readouterr().out
        assert "No comments" in output

    @patch("urllib.request.urlopen")
    def test_prints_no_comments_message_when_empty(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response([])
        args = MagicMock(iid=87)
        glab_harness_module.command_merge_request_discussions(
            args, "fake-token", "test/project", "git.coates.io"
        )
        output = capsys.readouterr().out
        assert "No comments" in output


class TestCommandMergeRequestChanges:
    @patch("urllib.request.urlopen")
    def test_lists_changed_files(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            {"changes": [{"new_path": "src/app.tsx"}, {"new_path": "src/layout.css"}]}
        )
        args = MagicMock(iid=88)
        glab_harness_module.command_merge_request_changes(
            args, "fake-token", "test/project", "git.coates.io"
        )
        output = capsys.readouterr().out
        assert "2 files changed" in output
        assert "src/app.tsx" in output


class TestCommandMergeRequestClose:
    @patch("urllib.request.urlopen")
    def test_closes_merge_request(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            {"iid": 83, "state": "closed"}
        )
        args = MagicMock(iid=83)
        glab_harness_module.command_merge_request_close(
            args, "fake-token", "test/project", "git.coates.io"
        )
        output = capsys.readouterr().out
        assert "!83 closed" in output


class TestCommandMergeRequestMerge:
    @patch("urllib.request.urlopen")
    def test_merges_merge_request(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            {"iid": 88, "state": "merged"}
        )
        args = MagicMock(iid=88, squash=False)
        glab_harness_module.command_merge_request_merge(
            args, "fake-token", "test/project", "git.coates.io"
        )
        output = capsys.readouterr().out
        assert "!88 merged" in output

    @patch("urllib.request.urlopen")
    def test_merges_with_squash(
        self, mock_urlopen, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            {"iid": 88, "state": "merged"}
        )
        args = MagicMock(iid=88, squash=True)
        glab_harness_module.command_merge_request_merge(
            args, "fake-token", "test/project", "git.coates.io"
        )
        sent_body = json.loads(mock_urlopen.call_args[0][0].data)
        assert sent_body["squash"] is True
