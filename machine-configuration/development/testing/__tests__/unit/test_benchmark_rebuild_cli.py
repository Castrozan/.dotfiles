from unittest.mock import MagicMock, patch

import pytest

import benchmark_rebuild


class TestMain:
    def test_report_command(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("timestamp,type,config,duration_seconds,commit\n")

        with (
            patch("benchmark_rebuild.sys.argv", ["cmd", "report"]),
            patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=results_file,
            ),
        ):
            benchmark_rebuild.main()

    def test_unknown_command_exits(self):
        with (
            patch("benchmark_rebuild.sys.argv", ["cmd", "bogus"]),
            patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=MagicMock(),
            ),
            patch("benchmark_rebuild.ensure_results_file_exists"),
        ):
            with pytest.raises(SystemExit) as exit_info:
                benchmark_rebuild.main()
            assert exit_info.value.code == 1

    def test_eval_command_runs_benchmark(self):
        with (
            patch("benchmark_rebuild.sys.argv", ["cmd", "eval"]),
            patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=MagicMock(),
            ),
            patch("benchmark_rebuild.ensure_results_file_exists"),
            patch("benchmark_rebuild.run_and_record_benchmark") as mock_bench,
        ):
            benchmark_rebuild.main()
            mock_bench.assert_called_once()
            assert mock_bench.call_args[0][0] == "eval"

    def test_all_command_runs_eval_and_dryrun(self):
        with (
            patch("benchmark_rebuild.sys.argv", ["cmd"]),
            patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=MagicMock(),
            ),
            patch("benchmark_rebuild.ensure_results_file_exists"),
            patch("benchmark_rebuild.run_and_record_benchmark") as mock_bench,
        ):
            benchmark_rebuild.main()
            assert mock_bench.call_count == 2
            types = [c[0][0] for c in mock_bench.call_args_list]
            assert "eval" in types
            assert "dry-run" in types

    def test_check_baseline_exits_zero_on_pass(self):
        with (
            patch("benchmark_rebuild.sys.argv", ["cmd", "--check-baseline"]),
            patch("benchmark_rebuild.check_baseline", return_value=True),
        ):
            with pytest.raises(SystemExit) as exit_info:
                benchmark_rebuild.main()
            assert exit_info.value.code == 0

    def test_check_baseline_exits_one_on_fail(self):
        with (
            patch("benchmark_rebuild.sys.argv", ["cmd", "--check-baseline"]),
            patch("benchmark_rebuild.check_baseline", return_value=False),
        ):
            with pytest.raises(SystemExit) as exit_info:
                benchmark_rebuild.main()
            assert exit_info.value.code == 1

    def test_check_baseline_needs_no_results_file(self):
        with (
            patch("benchmark_rebuild.sys.argv", ["cmd", "--check-baseline"]),
            patch("benchmark_rebuild.check_baseline", return_value=True),
            patch("benchmark_rebuild.ensure_results_file_exists") as mock_ensure,
        ):
            with pytest.raises(SystemExit):
                benchmark_rebuild.main()
            mock_ensure.assert_not_called()

    def test_save_baseline_calls_save(self):
        with (
            patch("benchmark_rebuild.sys.argv", ["cmd", "--save-baseline"]),
            patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=MagicMock(),
            ),
            patch("benchmark_rebuild.ensure_results_file_exists"),
            patch("benchmark_rebuild.save_baseline") as mock_save,
        ):
            benchmark_rebuild.main()
            mock_save.assert_called_once()

    def test_refused_save_baseline_exits_one(self):
        with (
            patch("benchmark_rebuild.sys.argv", ["cmd", "--save-baseline"]),
            patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=MagicMock(),
            ),
            patch("benchmark_rebuild.ensure_results_file_exists"),
            patch("benchmark_rebuild.save_baseline", return_value=False),
        ):
            with pytest.raises(SystemExit) as exit_info:
                benchmark_rebuild.main()
            assert exit_info.value.code == 1
