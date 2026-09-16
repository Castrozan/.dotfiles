from e2e.coaching.coached_models import CoachedSessionResult, failed_coached_session
from e2e.coaching.coached_reporting import print_coached_results
from integration.comparisons.ab_test_models import (
    AbTestResult,
    InstructionFollowingMetrics,
    SessionTrace,
)
from integration.comparisons.ab_test_reporting import print_ab_test_results


def test_comparison_report_aligns_missing_results_and_averages(capsys):
    results = [
        AbTestResult(
            configuration,
            "rename",
            InstructionFollowingMetrics(
                score=score, read_before_edit=score > 50, read_to_edit_ratio=0.5
            ),
            SessionTrace(),
            2,
        )
        for configuration, score in [("inline", 80), ("reference", 45), ("empty", 20)]
    ]
    print_ab_test_results(results, ["inline", "reference", "empty", "missing"])
    output = capsys.readouterr().out
    assert "N/A" in output
    assert "Read/edit ratio" in output
    assert "0.5" in output
    for score in [80, 45, 20]:
        assert f"{score}/100" in output
    assert output.count("time: 2s") == 3


def test_coached_report_retains_failures_and_aggregate_improvement(capsys):
    results = [
        CoachedSessionResult(
            "improved", 50, 80, 30, [], [], "FAIL: before\nPASS: after", 2
        ),
        CoachedSessionResult("regressed", 80, 50, -30, [], [], "", 1),
        failed_coached_session("failed", 3, "timeout"),
    ]
    print_coached_results(results)
    output = capsys.readouterr().out
    for fragment in [
        "FAIL: before",
        "PASS: after",
        "Error: timeout",
        "Initial: 43",
        "Coached: 43",
        "(+0)",
    ]:
        assert fragment in output
    print_coached_results([])
    assert "Initial: 0" in capsys.readouterr().out
