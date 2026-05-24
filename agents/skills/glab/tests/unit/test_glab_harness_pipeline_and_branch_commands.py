from unittest.mock import MagicMock, patch


class TestCommandPipelines:
    @patch("urllib.request.urlopen")
    def test_lists_pipelines(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            [
                {
                    "id": 1000,
                    "status": "success",
                    "source": "push",
                    "created_at": "2026-03-28T06:08:57Z",
                }
            ]
        )
        args = MagicMock(ref=None, count=5)
        glab_harness_module.command_pipelines(
            args, "fake-token", "test/project", "git.coates.io"
        )
        output = capsys.readouterr().out
        assert "#1000" in output
        assert "success" in output

    @patch("urllib.request.urlopen")
    def test_filters_by_ref(
        self, mock_urlopen, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response([])
        args = MagicMock(ref="release/uat", count=5)
        glab_harness_module.command_pipelines(
            args, "fake-token", "test/project", "git.coates.io"
        )
        sent_url = mock_urlopen.call_args[0][0].full_url
        assert "release" in sent_url


class TestCommandPipelineJobs:
    @patch("urllib.request.urlopen")
    def test_lists_jobs(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response(
            [
                {
                    "name": "build:uat",
                    "status": "success",
                    "stage": "build",
                    "finished_at": "2026-03-28T07:30:00Z",
                }
            ]
        )
        args = MagicMock(pipeline_id=1000)
        glab_harness_module.command_pipeline_jobs(
            args, "fake-token", "test/project", "git.coates.io"
        )
        output = capsys.readouterr().out
        assert "build:uat" in output
        assert "success" in output


class TestCommandDeleteBranch:
    @patch("urllib.request.urlopen")
    def test_deletes_branch_with_url_encoding(
        self, mock_urlopen, capsys, glab_harness_module, make_mock_http_response
    ):
        mock_urlopen.return_value = make_mock_http_response({})
        args = MagicMock(branch_name="release/uat-27-03-2026")
        glab_harness_module.command_delete_branch(
            args, "fake-token", "test/project", "git.coates.io"
        )
        sent_url = mock_urlopen.call_args[0][0].full_url
        assert "release%2Fuat-27-03-2026" in sent_url
        output = capsys.readouterr().out
        assert "deleted" in output
