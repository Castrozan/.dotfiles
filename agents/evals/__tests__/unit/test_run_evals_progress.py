import io

from run_evals_progress import EvaluationProgressReporter, format_duration
from run_evals_test_runner import TestResult


def result(name, passed=True, duration=1.0, category="core_rules"):
    return TestResult(
        name=name,
        passed=passed,
        duration=duration,
        output="",
        assertions_failed=[],
        category=category,
    )


def reporter_over(total=4):
    stream = io.StringIO()
    return EvaluationProgressReporter(total, max_workers=2, stream=stream), stream


def test_every_finished_test_emits_one_flushed_line_naming_its_category():
    reporter, stream = reporter_over()
    reporter.record(result("typo_inference", category="core_rules"))
    reporter.record(result("routing_to_nix", passed=False, category="skill_routing"))

    lines = stream.getvalue().strip().split("\n")
    assert len(lines) == 2
    assert "[1/4] ok" in lines[0] and "core_rules/typo_inference" in lines[0]
    assert "[2/4] FAIL" in lines[1] and "skill_routing/routing_to_nix" in lines[1]


def test_the_running_pass_rate_tracks_the_tests_finished_so_far():
    reporter, stream = reporter_over()
    reporter.record(result("a"))
    reporter.record(result("b", passed=False))
    reporter.record(result("c"))

    assert "pass-rate 66.7% (2/3)" in stream.getvalue().strip().split("\n")[-1]


def test_an_eta_appears_only_once_a_test_has_finished():
    reporter, _ = reporter_over()
    assert reporter.estimated_remaining_seconds() is None
    reporter.record(result("a"))
    assert reporter.estimated_remaining_seconds() is not None


def test_the_closing_summary_names_the_slowest_test():
    reporter, stream = reporter_over(total=2)
    reporter.record(result("quick_one", duration=0.5))
    reporter.record(result("slow_one", duration=91.0))
    reporter.announce_finish()

    summary = stream.getvalue().strip().split("\n")[-1]
    assert "2 passed, 0 failed" in summary
    assert "slowest slow_one 1m31s" in summary


def test_durations_are_readable_at_every_scale():
    assert format_duration(9.4) == "9s"
    assert format_duration(91) == "1m31s"
    assert format_duration(3700) == "1h01m"
