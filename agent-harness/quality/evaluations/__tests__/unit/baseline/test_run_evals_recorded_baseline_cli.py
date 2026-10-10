import importlib.util
import sys
from pathlib import Path

import pytest

from runner.run_evals_arguments import parse_arguments


def test_recorded_cli_checks_the_repository_before_any_model_provider(monkeypatch):
    script_path = Path(__file__).resolve().parents[3] / "run-evals.py"
    baseline_path = script_path.parent / "baseline.json"
    baseline_bytes = baseline_path.read_bytes()
    specification = importlib.util.spec_from_file_location(
        "evaluation_cli", script_path
    )
    evaluation_cli = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(evaluation_cli)
    monkeypatch.setattr(
        evaluation_cli,
        "resolve_node_runtime",
        lambda: pytest.fail("recorded checks must not resolve a provider runtime"),
    )
    monkeypatch.setattr(
        evaluation_cli,
        "_run_selected_evaluation",
        lambda *arguments: pytest.fail("recorded checks must not invoke a measurement"),
    )
    monkeypatch.setattr(sys, "argv", ["run-evals.py", "--check-recorded-baseline"])
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)

    with pytest.raises(SystemExit) as result:
        evaluation_cli.main()

    assert result.value.code == 0
    assert baseline_path.read_bytes() == baseline_bytes


@pytest.mark.parametrize(
    "measurement_argument",
    (
        "--save-baseline",
        "--save-ab-profile",
        "--ab",
        "--calibrate-judge",
        "--check-baseline",
    ),
)
def test_recorded_check_cannot_be_combined_with_measurement_modes(
    measurement_argument, monkeypatch
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["run-evals.py", "--check-recorded-baseline", measurement_argument],
    )

    with pytest.raises(SystemExit):
        parse_arguments()
