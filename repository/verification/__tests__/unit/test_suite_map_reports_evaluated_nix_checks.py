import json
import subprocess

import pytest


def evaluation_completing_with(return_code, standard_output):
    def run_evaluation(*_arguments, **_keyword_arguments):
        return subprocess.CompletedProcess([], return_code, standard_output, "")

    return run_evaluation


def evaluation_raising(error):
    def run_evaluation(*_arguments, **_keyword_arguments):
        raise error

    return run_evaluation


def test_a_successful_evaluation_reports_the_registered_check_attributes(
    load_suite_map,
):
    suite_map = load_suite_map()
    check_names = ["seanime-listens-on-loopback", "voice-model-is-pinned"]

    with pytest.MonkeyPatch.context() as patched:
        patched.setattr(
            suite_map.subprocess,
            "run",
            evaluation_completing_with(0, json.dumps(check_names)),
        )
        inventory = suite_map.evaluate_nix_check_inventory()

    assert inventory == suite_map.NixCheckInventory(tuple(check_names), None), (
        "the map must carry the evaluated attribute names themselves, because a "
        "bare number cannot be traced back to the checks nix actually registered"
    )
    assert suite_map.format_nix_check_total(inventory) == "2", (
        "the totals line reports how many checks the flake exposes, so it counts "
        "the evaluated attribute names rather than anything read out of source"
    )


def test_the_evaluation_asks_the_flake_for_the_current_systems_check_names(
    load_suite_map,
):
    suite_map = load_suite_map()
    recorded_invocations = []

    def record_invocation(command, **keyword_arguments):
        recorded_invocations.append((command, keyword_arguments))
        return subprocess.CompletedProcess([], 0, "[]", "")

    with pytest.MonkeyPatch.context() as patched:
        patched.setattr(suite_map.subprocess, "run", record_invocation)
        suite_map.evaluate_nix_check_inventory()

    command, keyword_arguments = recorded_invocations[0]
    assert len(recorded_invocations) == 1, (
        "one bounded evaluation covers the whole flake, so a per-module or "
        "per-check subprocess would multiply a six-second evaluation by every owner"
    )
    assert command[:5] == ["nix", "eval", "--json", "--impure", "--expr"], (
        "builtins.currentSystem only resolves in an impure evaluation, and the "
        "decoder needs JSON rather than the nix value printer"
    )
    assert "builtins.attrNames" in command[5] and "checks." in command[5], (
        "the inventory is the attribute-name list of the current system's checks; "
        "anything else stops describing what nix would actually build"
    )
    assert keyword_arguments["cwd"] == suite_map.REPOSITORY_ROOT, (
        "the evaluation is rooted at the checkout, so a drifted shell directory "
        "cannot silently inventory a sibling worktree's flake"
    )
    assert (
        keyword_arguments["timeout"] == suite_map.NIX_CHECK_INVENTORY_TIMEOUT_SECONDS
    ), "an unbounded evaluation would hang the map forever on a stuck nix daemon"


def test_a_wrapper_that_only_imports_its_cases_is_still_registered(
    tmp_path, load_suite_map
):
    suite_map = load_suite_map()
    tests_directory = tmp_path / "__tests__"
    tests_directory.mkdir()
    (tests_directory / "checks.nix").write_text("args: import ./seanime.nix args\n")

    summary = suite_map.summarize_tests_directory(tests_directory)

    assert summary["has_checks_nix"], (
        "a wrapper that imports its cases owns real checks, so the map must see "
        "the file rather than the function names spelled inside it"
    )
    assert suite_map.format_summary_lines(summary) == ["    checks.nix: registered"], (
        "counting literal mkEvalCheck calls reported zero for every wrapper that "
        "imports a large check set, which read as an untested module while nix "
        "flake check was evaluating all of its checks"
    )


@pytest.mark.parametrize(
    "failing_evaluation, expected_reason",
    [
        (evaluation_raising(FileNotFoundError()), "nix is not installed"),
        (
            evaluation_raising(subprocess.TimeoutExpired("nix", 300)),
            "evaluation timed out",
        ),
        (evaluation_completing_with(1, ""), "exit status 1"),
        (
            evaluation_completing_with(0, "error: attribute missing"),
            "invalid JSON output",
        ),
        (
            evaluation_completing_with(0, json.dumps({"seanime": {}})),
            "non-list evaluation result",
        ),
    ],
)
def test_an_unusable_evaluation_never_reports_zero_checks(
    failing_evaluation, expected_reason, load_suite_map
):
    suite_map = load_suite_map()

    with pytest.MonkeyPatch.context() as patched:
        patched.setattr(suite_map.subprocess, "run", failing_evaluation)
        inventory = suite_map.evaluate_nix_check_inventory()

    assert inventory.check_names is None, (
        "an evaluation that produced no inventory has no attribute names, and "
        "an empty list here would be indistinguishable from a flake with no checks"
    )
    assert (
        suite_map.format_nix_check_total(inventory)
        == f"unavailable ({expected_reason})"
    ), (
        "the totals line must say the number is missing and why, because printing "
        "zero would report a fully covered repository as having no nix checks"
    )


def test_the_map_separates_registered_modules_from_the_evaluated_total(
    tmp_path, capsys, load_suite_map
):
    suite_map = load_suite_map()
    wrapper_tests_directory = tmp_path / "voice" / "__tests__"
    wrapper_tests_directory.mkdir(parents=True)
    (wrapper_tests_directory / "checks.nix").write_text(
        "args: import ./cases.nix args\n"
    )

    with pytest.MonkeyPatch.context() as patched:
        patched.setattr(suite_map, "REPOSITORY_ROOT", tmp_path)
        patched.setattr(
            suite_map,
            "evaluate_nix_check_inventory",
            lambda: suite_map.NixCheckInventory(("first-check", "second-check"), None),
        )
        suite_map.main()

    printed_map = capsys.readouterr().out

    assert "voice\n    checks.nix: registered\n" in printed_map, (
        "each owner reports that its check module is registered, because the "
        "per-owner share of an evaluated flake inventory is not knowable from disk"
    )
    assert "  modules with tests: 1\n" in printed_map, (
        "one owner registered its checks, and the owner tally counts modules "
        "rather than the checks their modules register"
    )
    assert "  nix checks:         2\n" in printed_map, (
        "the evaluated total counts the flake's check attributes, so it stays "
        "independent of how many modules registered a checks.nix"
    )
