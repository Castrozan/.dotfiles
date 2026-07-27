from pathlib import Path

import yaml

from run_evals_hook_test_runner import find_hook_script

EVAL_SUITE_DIRECTORY = Path(__file__).resolve().parents[1] / "evals"


def hook_references_declared_by_every_suite():
    for suite in sorted(EVAL_SUITE_DIRECTORY.glob("*.yaml")):
        for test in yaml.safe_load(suite.read_text()).get("tests") or []:
            if test.get("hook"):
                yield suite.name, test["name"], test["hook"]


def test_the_sweep_finds_hooks_to_check():
    assert list(hook_references_declared_by_every_suite()), (
        "no eval suite declares a hook, so the resolution guard below would pass "
        "without checking anything"
    )


def test_every_hook_named_by_any_eval_suite_resolves():
    unresolved = [
        f"{suite}:{name} names {hook}"
        for suite, name, hook in hook_references_declared_by_every_suite()
        if find_hook_script(hook) is None
    ]
    assert not unresolved, (
        "eval suites name hook scripts that no longer exist; a case whose hook "
        f"cannot be resolved asserts nothing about the guard it claims to cover: "
        f"{unresolved}"
    )
