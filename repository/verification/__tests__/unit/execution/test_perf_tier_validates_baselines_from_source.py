import pytest

from perf_tier_baseline_harness import (
    BASELINE_FILE_NAME_PER_TIER_FUNCTION,
    STALE_GENERATED_AT,
    checkout_with_baseline,
    command_poor_bin_directory,
    run_tier_function,
    tracked_baseline,
)


@pytest.mark.parametrize(
    ("tier_function", "baseline_file_name"),
    sorted(BASELINE_FILE_NAME_PER_TIER_FUNCTION.items()),
)
def test_the_check_validates_the_source_baseline_without_the_installed_command(
    tmp_path, tier_function, baseline_file_name
):
    bin_directory = command_poor_bin_directory(tmp_path)
    checkout_root = checkout_with_baseline(
        tmp_path, baseline_file_name, tracked_baseline(baseline_file_name)
    )

    completed = run_tier_function(tier_function, checkout_root, bin_directory)

    assert completed.returncode == 0, (
        f"{tier_function} must validate {baseline_file_name} straight from the "
        "repository sources, because continuous integration never has the packaged "
        f"benchmark command on PATH.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
    assert "SKIP" not in completed.stdout + completed.stderr, (
        "a skip here is the hole this check closes: the tier would report green "
        "without reading either baseline.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )


@pytest.mark.parametrize(
    ("tier_function", "baseline_file_name"),
    sorted(BASELINE_FILE_NAME_PER_TIER_FUNCTION.items()),
)
def test_the_check_propagates_an_invalid_source_baseline_as_a_failure(
    tmp_path, tier_function, baseline_file_name
):
    bin_directory = command_poor_bin_directory(tmp_path)
    unattributed_baseline = tracked_baseline(baseline_file_name)
    del unattributed_baseline["host"]
    checkout_root = checkout_with_baseline(
        tmp_path, baseline_file_name, unattributed_baseline
    )

    completed = run_tier_function(tier_function, checkout_root, bin_directory)

    assert completed.returncode != 0, (
        f"{tier_function} must return the validator's exit code, otherwise the "
        "trailing echo becomes the function's status and an unusable baseline reads "
        "as a pass once the tier runner drops errexit.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
    assert "Baseline has no recorded host." in completed.stdout, (
        "the failure must name what is wrong with the tracked baseline.\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )


@pytest.mark.parametrize(
    ("tier_function", "baseline_file_name"),
    sorted(BASELINE_FILE_NAME_PER_TIER_FUNCTION.items()),
)
def test_a_stale_baseline_fails_only_where_it_can_be_recaptured(
    tmp_path, tier_function, baseline_file_name
):
    bin_directory = command_poor_bin_directory(tmp_path)
    checkout_root = checkout_with_baseline(
        tmp_path,
        baseline_file_name,
        tracked_baseline(baseline_file_name, generated_at=STALE_GENERATED_AT),
    )

    integration = run_tier_function(tier_function, checkout_root, bin_directory)
    owning_host = run_tier_function(
        tier_function, checkout_root, bin_directory, "--require-fresh"
    )

    assert integration.returncode == 0, (
        "continuous integration can never recapture a host measurement, so a stale "
        "tracked baseline must not turn the repository red on a calendar.\n"
        f"stdout: {integration.stdout}\nstderr: {integration.stderr}"
    )
    assert owning_host.returncode != 0, (
        "the performance tier runs on the owning host, the one place that can "
        "recapture the measurement, so staleness must fail there.\n"
        f"stdout: {owning_host.stdout}\nstderr: {owning_host.stderr}"
    )
    assert "days old" in owning_host.stdout, (
        "the failure must name the age that made the tracked baseline unusable.\n"
        f"stdout: {owning_host.stdout}\nstderr: {owning_host.stderr}"
    )
