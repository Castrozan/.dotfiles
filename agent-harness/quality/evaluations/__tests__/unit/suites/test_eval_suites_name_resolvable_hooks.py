import shlex

from evaluation_suite_support import every_authored_case
from instructions.instruction_surface_scanner import REPO_ROOT

HOOK_RUNTIME_ROOT = REPO_ROOT / "agent-harness" / "hooks" / "runtime"
HOOK_VERDICT_SCRIPT = "hook-verdict.py"


def hook_references_declared_by_every_suite():
    for suite_path, case in every_authored_case():
        if case.get("tipo") != "cli":
            continue
        arguments = shlex.split(case["comando"])
        if not any(argument.endswith(HOOK_VERDICT_SCRIPT) for argument in arguments):
            continue
        yield suite_path.name, case["nome"], arguments[-1]


def test_the_sweep_finds_hooks_to_check():
    assert list(hook_references_declared_by_every_suite()), (
        "no suite declares a hook case, so the resolution guard below would pass "
        "without checking anything"
    )


def test_every_hook_named_by_any_suite_resolves():
    unresolved = [
        f"{suite}:{name} names {hook}"
        for suite, name, hook in hook_references_declared_by_every_suite()
        if not list(HOOK_RUNTIME_ROOT.rglob(hook))
    ]
    assert not unresolved, (
        "suites name hook scripts that no longer exist; a case whose hook cannot be "
        f"resolved asserts nothing about the guard it claims to cover: {unresolved}"
    )
