"""The module count each hook invocation is allowed to pay.

The budget is the reproducible half of hook cost: wall time moves with the
machine, but the set of modules an invocation imports does not. What each
number means, and what it takes to raise one, is in
dispatcher_import_measurement.py alongside the table itself.
"""

import pytest
from dispatcher_import_measurement import (
    INVOCATIONS_UNDER_BUDGET,
    modules_imported_by,
)


@pytest.mark.parametrize("invocation_name", sorted(INVOCATIONS_UNDER_BUDGET))
def test_every_hook_invocation_stays_within_its_module_budget(invocation_name):
    dispatcher_name, payload, budget = INVOCATIONS_UNDER_BUDGET[invocation_name]
    imported = modules_imported_by(dispatcher_name, payload)
    assert len(imported) <= budget, (
        f"{invocation_name} imported {len(imported)} modules against a budget of "
        f"{budget}. Every import is a stat, a read and an unmarshal in a process "
        "that lives for milliseconds and runs on every matching tool call, so the "
        "module count is the reproducible proxy for what the hook costs. Find what "
        "landed on this path and either move it behind its matcher or justify the "
        "raise with a measurement."
    )
