import benchmark_rebuild


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
        assert "--save-baseline" in output
        assert "--check-baseline" in output
