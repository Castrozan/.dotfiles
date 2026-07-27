---
name: test
description: Testing methodology and verification workflow. Use when implementing, fixing, or modifying any code. Defines the test-first, test-after, and pre-delivery verification protocol.
---

<philosophy>
You own testing. Never delegate testing to the user. Never present untested code. Never skip tests because "it's a small
change." Every change gets tested by you before the user sees it. If you can't test due to environment limitations,
explain the constraint and ask for help.
</philosophy>

<before_changes>
Test first to establish baseline. Before modifying any code, run existing tests to capture current behavior. Understand
what passes and what fails before touching anything. This baseline tells you what behavior to preserve and what's
already broken. Read relevant test files. Run the test suite for the affected area. Note expected outputs. This prevents
introducing regressions and gives you a clear picture of the contract you must maintain.
</before_changes>

<after_changes>
Commit and push after every change, so the suite runs where it is the gate. A test that passes locally and fails on CI,
or fails on one CI run and passes on the next, is a race or a state leak in the test rather than infrastructure noise;
diagnose and fix it instead of re-pushing until it goes green. Commit before the verification so the change is tracked
regardless of the outcome.
</after_changes>

<pre_delivery>
Before presenting results to the user, stop and verify completeness:
1. Re-read the user's original request from conversation history. What exactly did they ask for?
2. Compare your implementation against every point in their request. Did you miss anything? Did you add anything they
   didn't ask for?
3. Push the complete change set, not just the last file you touched, and wait out every CI run with `gh run watch`.
4. Only after CI is green for that commit, present your work to the user.
</pre_delivery>

<what_to_test>
In the dotfiles repo, CI is the test gate: pushing runs the script tiers and `nix flake check` on GitHub Actions, and
`gh run list --commit $(git rev-parse HEAD) --json databaseId,name,conclusion` then `gh run watch <id> --exit-status` on
each id is how you wait it out, so a local full-suite pass is not what proves a change. Do
not run `__tests__/run.sh` as a gate before responding. Run it when it earns its wall time: to reproduce a job CI turned
red, to iterate on a test you are writing, or to exercise a tier CI cannot reach. The integration and runtime tiers need
the live machine, so a nightly job runs them at 03:00 rather than any interactive session.

For fast iteration on a single file, run `pytest` or `bats` directly: both are globally installed and should be on PATH.
Only fall back to `nix shell` if they are genuinely missing.

Every tier and every CI job reports all of its failures instead of dying on the first, so read the whole output and fix
the batch in one pass.
</what_to_test>

<test_failures>
Fix immediately. Do not just report a failure: diagnose and fix it. Re-test after the fix with the double-test protocol.
If you cannot fix the failure, explain what you tried, what you found, and ask the user for guidance. Never leave tests
broken and move on.
</test_failures>
