---
name: quality-assurance
description: Final QA method: verify finished work against the user's stated goal, widen the scope past the tests the plan named, and hunt side effects in untouched behavior.
---

<verify-the-goal-not-the-diff>
Start from the user's own words, not the implementer's summary of them. Every stated requirement gets met or not met
plus the evidence that settled it. The requirement nobody translated into a test is the one most likely unmet, so find
those first.
</verify-the-goal-not-the-diff>

<widen-past-the-specified-tests>
The plan's tests are the floor. Add the boundary, empty, malformed and duplicate inputs of every changed path, every
caller of every changed signature, repeated and concurrent invocation, and the failure paths the happy-path tests
skip. Exercise the interface the user touches, not only the unit that changed.
</widen-past-the-specified-tests>

<hunt-side-effects>
Assume the change leaked. Exercise the behavior beside it that was supposed to stay identical, the shared state it
writes, the ordering it may have altered, and everything else reading the same file, table, socket or environment
variable. Run the suites the change did not target.
</hunt-side-effects>

<report-do-not-repair>
Never fix what you find. Give the exact reproduction: command, input, observed output, expected output. Close with one
verdict on whether the user's goal is achieved and what is missing if it is not. The `test` skill owns when and where
the suite runs.
</report-do-not-repair>
