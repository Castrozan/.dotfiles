from unittest.mock import patch, MagicMock

import benchmark_rebuild


class TestMain:
    def test_report_command(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("timestamp,type,config,duration_seconds,commit\n")

        with patch("benchmark_rebuild.sys.argv", ["cmd", "report"]):
            with patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=results_file,
            ):
                benchmark_rebuild.main()

    def test_unknown_command_exits(self):
        with patch("benchmark_rebuild.sys.argv", ["cmd", "bogus"]):
            with patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=MagicMock(),
            ):
                with patch("benchmark_rebuild.ensure_results_directory_exists"):
                    with patch("benchmark_rebuild.initialize_csv_if_needed"):
                        try:
                            benchmark_rebuild.main()
                            assert False, "Should have raised SystemExit"
                        except SystemExit as e:
                            assert e.code == 1

    def test_eval_command_runs_benchmark(self):
        with patch("benchmark_rebuild.sys.argv", ["cmd", "eval"]):
            with patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=MagicMock(),
            ):
                with patch("benchmark_rebuild.ensure_results_directory_exists"):
                    with patch("benchmark_rebuild.initialize_csv_if_needed"):
                        with patch(
                            "benchmark_rebuild.run_and_record_benchmark"
                        ) as mock_bench:
                            benchmark_rebuild.main()
                            mock_bench.assert_called_once()
                            assert mock_bench.call_args[0][0] == "eval"

    def test_all_command_runs_eval_and_dryrun(self):
        with patch("benchmark_rebuild.sys.argv", ["cmd"]):
            with patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=MagicMock(),
            ):
                with patch("benchmark_rebuild.ensure_results_directory_exists"):
                    with patch("benchmark_rebuild.initialize_csv_if_needed"):
                        with patch(
                            "benchmark_rebuild.run_and_record_benchmark"
                        ) as mock_bench:
                            benchmark_rebuild.main()
                            assert mock_bench.call_count == 2
                            types = [c[0][0] for c in mock_bench.call_args_list]
                            assert "eval" in types
                            assert "dry-run" in types

    def test_check_baseline_exits_zero_on_pass(self, tmp_path):
        with patch(
            "benchmark_rebuild.sys.argv",
            ["cmd", "--check-baseline"],
        ):
            with patch(
                "benchmark_rebuild.check_baseline",
                return_value=True,
            ):
                try:
                    benchmark_rebuild.main()
                    assert False, "Should have raised SystemExit"
                except SystemExit as e:
                    assert e.code == 0

    def test_check_baseline_exits_one_on_fail(self):
        with patch(
            "benchmark_rebuild.sys.argv",
            ["cmd", "--check-baseline"],
        ):
            with patch(
                "benchmark_rebuild.check_baseline",
                return_value=False,
            ):
                try:
                    benchmark_rebuild.main()
                    assert False, "Should have raised SystemExit"
                except SystemExit as e:
                    assert e.code == 1

    def test_save_baseline_calls_save(self):
        with patch(
            "benchmark_rebuild.sys.argv",
            ["cmd", "--save-baseline"],
        ):
            with patch(
                "benchmark_rebuild.get_results_file_path",
                return_value=MagicMock(),
            ):
                with patch("benchmark_rebuild.ensure_results_directory_exists"):
                    with patch("benchmark_rebuild.initialize_csv_if_needed"):
                        with patch("benchmark_rebuild.save_baseline") as mock_save:
                            benchmark_rebuild.main()
                            mock_save.assert_called_once()
