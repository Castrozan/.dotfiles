---
name: test
description: Testing methodology and verification workflow. Use when implementing, fixing, or modifying any code. Defines the test-first, test-after, and pre-delivery verification protocol.
---

<philosophy>
You own testing. Never delegate testing to the user. Never present untested code. Never skip tests because "it's a small change." Every change gets tested by you before the user sees it. If you can't test due to environment limitations, explain the constraint and ask for help.
</philosophy>

<before_changes>
Test first to establish baseline. Before modifying any code, run existing tests to capture current behavior. Understand what passes and what fails before touching anything. This baseline tells you what behavior to preserve and what's already broken. Read relevant test files. Run the test suite for the affected area. Note expected outputs. This prevents introducing regressions and gives you a clear picture of the contract you must maintain.
</before_changes>

<after_changes>
Double-test after every change. Run the full relevant test suite once. Then run it again. Two consecutive passes confirm your change is stable, not flaky. If the first pass succeeds but the second fails, you have a race condition or state leak — fix it before proceeding. Commit between the change and the tests so the change is tracked regardless of test outcome.
</after_changes>

<pre_delivery>
Before presenting results to the user, stop and verify completeness:
1. Re-read the user's original request from conversation history. What exactly did they ask for?
2. Compare your implementation against every point in their request. Did you miss anything? Did you add anything they didn't ask for?
3. Run 2 final test passes against the complete change set — not just the last file you touched, but everything affected.
4. Only after both passes succeed, present your work to the user.
</pre_delivery>

<what_to_test>
`tests/run.sh` is the canonical entry point — run it with no args to see available tiers. Default workflow: quick after every change, `--nix` when touching `.nix` files, `--all` before delivery.

For fast iteration on a single file, run `pytest` or `bats` directly — both are globally installed and should be on PATH. Only fall back to `nix shell` if they are genuinely missing.
</what_to_test>

<test_failures>
Fix immediately. Do not just report a failure — diagnose and fix it. Re-test after the fix with the double-test protocol. If you cannot fix the failure, explain what you tried, what you found, and ask the user for guidance. Never leave tests broken and move on.
</test_failures>
