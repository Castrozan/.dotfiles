from e2e_assertions import run_e2e_assertions
from e2e_models import TerminalSessionTrace


def test_optional_empty_assertions_do_not_break_scenario_execution():
    trace = TerminalSessionTrace(
        raw_terminal_output="",
        detected_bash_commands=[],
        duration_seconds=0.0,
        timed_out=False,
    )

    assert run_e2e_assertions(trace, {"wrong_skill_not_invoked": None}) == []
