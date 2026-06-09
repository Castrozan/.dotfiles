from steward_test_helpers import steward_activate


def test_parse_health_check_results_classifies_pass_and_fail():
    output = (
        "  \x1b[32m✓\x1b[0m [daemon] clawde service (systemd)\n"
        "  \x1b[31m✗\x1b[0m [secret] agenix: api-keys/openai-api-key\n"
        "45/45 passed (0 failed)\n"
    )
    results = steward_activate.parse_health_check_results(output)
    assert results["[daemon] clawde service (systemd)"] is True
    assert results["[secret] agenix: api-keys/openai-api-key"] is False
    assert "45/45 passed (0 failed)" not in results


def test_regressions_are_checks_that_passed_before_and_fail_after():
    health_before = {"daemon a": True, "daemon b": True, "secret c": False}
    health_after = {"daemon a": True, "daemon b": False, "secret c": False}
    assert steward_activate.compute_activation_regressions(
        health_before, health_after
    ) == ["daemon b"]


def test_a_check_already_failing_before_is_not_a_regression():
    health_before = {"daemon a": False}
    health_after = {"daemon a": False}
    assert (
        steward_activate.compute_activation_regressions(health_before, health_after)
        == []
    )


def test_a_newly_appearing_failing_check_is_not_counted_as_regression():
    health_before = {"daemon a": True}
    health_after = {"daemon a": True, "daemon b": False}
    assert (
        steward_activate.compute_activation_regressions(health_before, health_after)
        == []
    )
