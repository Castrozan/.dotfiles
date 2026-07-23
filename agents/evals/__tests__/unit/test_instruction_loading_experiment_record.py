import json
from datetime import datetime
from pathlib import Path

EXPERIMENT_RECORD_PATH = (
    Path(__file__).resolve().parents[2] / "instruction-loading-experiment.json"
)
REQUIRED_CATEGORY_FIELDS = (
    "paired_tests",
    "pass_rate_with_instructions",
    "pass_rate_without_instructions",
    "delta",
    "instructions_only_wins",
    "control_only_wins",
    "mcnemar_exact_p_value",
    "significant",
)


def experiment_record() -> dict:
    return json.loads(EXPERIMENT_RECORD_PATH.read_text())


def test_the_experiment_record_exists_and_names_its_provenance():
    record = experiment_record()
    assert record["git_commit"], "the record must name the commit it was measured at"
    assert datetime.fromisoformat(record["generated_at"])
    assert record["method"], "the record must state how the arms were compared"
    assert record["finding"], "a result nobody read the meaning of is not recorded"


def test_every_measured_category_carries_a_complete_paired_result():
    categories = experiment_record()["categories"]
    assert categories, "the record measures no category, so it records nothing"
    for category_name, measurement in categories.items():
        for field in REQUIRED_CATEGORY_FIELDS:
            assert field in measurement, f"{category_name} is missing {field}"
        assert measurement["paired_tests"] > 0, f"{category_name} paired nothing"


def test_each_recorded_delta_matches_its_own_arms():
    for category_name, measurement in experiment_record()["categories"].items():
        expected_delta = (
            measurement["pass_rate_with_instructions"]
            - measurement["pass_rate_without_instructions"]
        )
        assert abs(measurement["delta"] - expected_delta) < 0.005, (
            f"{category_name} reports a delta that does not follow from its own arms"
        )


def test_stripping_the_instruction_surface_never_won_a_paired_test():
    for category_name, measurement in experiment_record()["categories"].items():
        assert measurement["control_only_wins"] == 0, (
            f"{category_name} recorded a test that passes only with the instruction "
            f"surface removed, which means those instructions actively hurt it"
        )


def test_significance_is_not_claimed_beyond_the_recorded_p_value():
    alpha = experiment_record()["significance_alpha"]
    for category_name, measurement in experiment_record()["categories"].items():
        claimed = measurement["significant"]
        supported = measurement["mcnemar_exact_p_value"] < alpha
        assert claimed == supported, (
            f"{category_name} claims significance={claimed} against p="
            f"{measurement['mcnemar_exact_p_value']} at alpha {alpha}"
        )
