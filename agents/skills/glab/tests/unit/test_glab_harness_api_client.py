import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest


class TestGitlabApiRequest:
    @patch("urllib.request.urlopen")
    def test_get_request_returns_parsed_json(
        self, mock_urlopen, glab_harness_module, make_mock_http_response
    ):
        expected_response = {"id": 1, "name": "test"}
        mock_urlopen.return_value = make_mock_http_response(expected_response)
        result = glab_harness_module.gitlab_api_request(
            "GET",
            "projects/123/merge_requests/1",
            "fake-token",
            host="git.coates.io",
        )
        assert result == expected_response

    @patch("urllib.request.urlopen")
    def test_post_request_sends_json_body(
        self, mock_urlopen, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response({"iid": 42})
        glab_harness_module.gitlab_api_request(
            "POST",
            "projects/123/merge_requests",
            "fake-token",
            body={"title": "Test"},
            host="git.coates.io",
        )
        sent_request = mock_urlopen.call_args[0][0]
        assert sent_request.method == "POST"
        assert json.loads(sent_request.data) == {"title": "Test"}
        assert sent_request.headers["Content-type"] == "application/json"

    @patch("urllib.request.urlopen")
    def test_includes_private_token_header(
        self, mock_urlopen, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response({})
        glab_harness_module.gitlab_api_request(
            "GET", "test", "my-secret-token", host="git.coates.io"
        )
        sent_request = mock_urlopen.call_args[0][0]
        assert sent_request.headers["Private-token"] == "my-secret-token"

    @patch("urllib.request.urlopen")
    def test_uses_host_in_url(
        self, mock_urlopen, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response({})
        glab_harness_module.gitlab_api_request(
            "GET", "projects/1", "fake-token", host="gitlab.com"
        )
        sent_request = mock_urlopen.call_args[0][0]
        assert sent_request.full_url.startswith("https://gitlab.com/api/v4/")

    @patch("urllib.request.urlopen")
    def test_exits_on_http_error(self, mock_urlopen, glab_harness_module):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="test",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=MagicMock(read=lambda: b'{"message":"not found"}'),
        )
        with pytest.raises(SystemExit):
            glab_harness_module.gitlab_api_request(
                "GET", "bad-endpoint", "fake-token", host="git.coates.io"
            )


class TestResolveUsernameToId:
    @patch("urllib.request.urlopen")
    def test_resolves_single_username(
        self, mock_urlopen, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            [{"id": 5, "username": "bob"}]
        )
        assert (
            glab_harness_module.resolve_username_to_id(
                "bob", "fake-token", "git.coates.io"
            )
            == 5
        )

    @patch("urllib.request.urlopen")
    def test_returns_none_for_unknown_username(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response([])
        assert (
            glab_harness_module.resolve_username_to_id(
                "nobody", "fake-token", "git.coates.io"
            )
            is None
        )
        assert "not found" in capsys.readouterr().err


class TestResolveCommaSeparatedUsernamesToIds:
    @patch("urllib.request.urlopen")
    def test_resolves_multiple_usernames(
        self, mock_urlopen, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.side_effect = [
            make_mock_http_response([{"id": 5, "username": "bob"}]),
            make_mock_http_response([{"id": 8, "username": "carol"}]),
        ]
        assert glab_harness_module.resolve_comma_separated_usernames_to_ids(
            "bob,carol", "fake-token", "git.coates.io"
        ) == [5, 8]
