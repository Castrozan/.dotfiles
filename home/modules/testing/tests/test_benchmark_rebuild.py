from unittest.mock import patch, MagicMock

import benchmark_rebuild


class TestDetectConfigurationType:
    def test_returns_nixos_when_nixos_directory_and_hostname_match(self, tmp_path):
        hostname_file = tmp_path / "hostname"
        hostname_file.write_text("zanoni\n")
        nixos_dir = tmp_path / "nixos"
        nixos_dir.mkdir()

        with patch("benchmark_rebuild.Path") as mock_path_cls:
            mock_path_cls.return_value = mock_path_cls
            mock_path_cls.__truediv__ = lambda self, key: {
                "hostname": hostname_file,
                "nixos": nixos_dir,
            }.get(key, tmp_path / key)

            real_path = __import__("pathlib").Path

            def path_factory(p):
                if p == "/etc/hostname":
                    return real_path(hostname_file)
                if p == "/etc/nixos":
                    return real_path(nixos_dir)
                return real_path(p)

            with patch(
                "benchmark_rebuild.Path",
                side_effect=path_factory,
            ):
                result = benchmark_rebuild.detect_configuration_type()
                assert result == "nixos"

    def test_returns_home_when_no_nixos_directory(self):
        with patch(
            "benchmark_rebuild.Path",
        ) as mock_path:
            mock_path.return_value.read_text.side_effect = FileNotFoundError
            result = benchmark_rebuild.detect_configuration_type()
            assert result == "home"


class TestGetFlakeOutputForConfiguration:
    def test_returns_nixos_output(self):
        result = benchmark_rebuild.get_flake_output_for_configuration("nixos")
        assert "nixosConfigurations" in result

    def test_returns_home_output_for_home(self):
        result = benchmark_rebuild.get_flake_output_for_configuration("home")
        assert "homeConfigurations" in result

    def test_returns_home_output_for_unknown(self):
        result = benchmark_rebuild.get_flake_output_for_configuration("other")
        assert "homeConfigurations" in result


class TestGetCurrentGitShortCommit:
    def test_returns_commit_hash(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "abc1234\n"
        with patch(
            "benchmark_rebuild.subprocess.run",
            return_value=mock_result,
        ):
            assert benchmark_rebuild.get_current_git_short_commit() == "abc1234"

    def test_returns_unknown_on_failure(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch(
            "benchmark_rebuild.subprocess.run",
            return_value=mock_result,
        ):
            assert benchmark_rebuild.get_current_git_short_commit() == "unknown"


class TestRunBenchmarkCommand:
    def test_returns_elapsed_time(self):
        with patch("benchmark_rebuild.subprocess.run"):
            duration = benchmark_rebuild.run_benchmark_command("echo test")
            assert isinstance(duration, float)
            assert duration >= 0


class TestRecordBenchmarkResult:
    def test_appends_csv_line(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("timestamp,type,config,duration_seconds,commit\n")

        benchmark_rebuild.record_benchmark_result(
            results_file, "eval", "home", 1.234, "abc1234"
        )

        content = results_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert "eval" in lines[1]
        assert "home" in lines[1]
        assert "1.234" in lines[1]
        assert "abc1234" in lines[1]


class TestInitializeCsvIfNeeded:
    def test_creates_file_with_header(self, tmp_path):
        results_file = tmp_path / "results.csv"
        benchmark_rebuild.initialize_csv_if_needed(results_file)
        content = results_file.read_text()
        assert content.startswith("timestamp,type,config")

    def test_does_not_overwrite_existing(self, tmp_path):
        results_file = tmp_path / "results.csv"
        results_file.write_text("existing data\n")
        benchmark_rebuild.initialize_csv_if_needed(results_file)
        assert results_file.read_text() == "existing data\n"


class TestPrintRecentResults:
    def test_prints_results(self, tmp_path, capsys):
        results_file = tmp_path / "results.csv"
        results_file.write_text(
            "timestamp,type,config,duration_seconds,commit\n"
            "2026-03-10T10:00:00+00:00,eval,home,1.234,abc1234\n"
        )
        benchmark_rebuild.print_recent_results(results_file)
        output = capsys.readouterr().out
        assert "Recent Benchmark Results" in output
        assert "eval" in output

    def test_handles_missing_file(self, tmp_path, capsys):
        results_file = tmp_path / "nonexistent.csv"
        benchmark_rebuild.print_recent_results(results_file)
        output = capsys.readouterr().out
        assert "No benchmark results found" in output

    def test_handles_empty_csv(self, tmp_path, capsys):
        results_file = tmp_path / "results.csv"
        results_file.write_text("timestamp,type,config,duration_seconds,commit\n")
        benchmark_rebuild.print_recent_results(results_file)
        output = capsys.readouterr().out
        assert "No benchmark results found" in output


class TestPrintAveragesByType:
    def test_computes_averages(self, capsys):
        data_lines = [
            "2026-03-10T10:00:00+00:00,eval,home,1.0,abc",
            "2026-03-10T10:01:00+00:00,eval,home,3.0,abc",
        ]
        benchmark_rebuild.print_averages_by_type(data_lines)
        output = capsys.readouterr().out
        assert "2.00s avg" in output
        assert "2 runs" in output

    def test_handles_malformed_lines(self, capsys):
        data_lines = ["bad,line"]
        benchmark_rebuild.print_averages_by_type(data_lines)
        output = capsys.readouterr().out
        assert "Averages by Type" in output


class TestPrintUsage:
    def test_prints_usage(self, capsys):
        benchmark_rebuild.print_usage()
        output = capsys.readouterr().out
        assert "benchmark-rebuild" in output
        assert "eval" in output
        assert "dry-run" in output
        assert "build" in output
        assert "report" in output


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
