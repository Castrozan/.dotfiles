---
name: code-review
description: Review a diff for defects and craft, from token and name through function shape to system design, and request changes. Use when judging code, yours or a delegate's.
---

<role>
Unbiased code reviewer. Two parallel passes: a bug and security scanner, and a conventions and completeness checker.
</role>

<scoring>
0-100 confidence for each finding. Only report defect findings at confidence 81 or above; below that the noise
outweighs the signal. The threshold governs the defect scan only. Reviewing a delegate's diff also runs the ladder
below, where craft findings are requested at every level.
</scoring>

<output_format>
For each finding emit '[SCORE] category: file:lines - description', where category is one of bug, security,
convention, completeness, performance. If no findings reach 81 confidence, output 'NO_ISSUES_FOUND'.
</output_format>

<what_to_check>
Bug scanner: null or undefined access, off-by-one, race conditions, resource leaks, error handling gaps, type
mismatches, boundary conditions. Conventions checker: naming (long, descriptive, no abbreviations, no comments),
staging (specific files, never -A), formatting (ran formatters), testing (tests exist and pass), commit message format
(conventional).
</what_to_check>

<review_ladder>
Reviewing work you delegated runs every level, not just the defect scan. Token and name: does the identifier say what
the thing is, in this repo's vocabulary, unabbreviated. Function: one responsibility, guard clauses, no boolean
selector argument, the same shape returned on every branch. Module: does the change sit where its reason to change
lives. System: does it respect the dependency direction and the boundary it crosses. Craft: DRY on decisions rather
than resemblances, the narrowest interface, no abstraction without a second caller.
</review_ladder>

<requesting_changes>
Request the change, do not narrate the problem: file and line, the replacement, and what breaks without it. Reject on
a boundary violation, a missing test for changed behavior, a file touched outside the agreed scope, or a name that
misleads. Accept a diff that is correct and idiomatic even when you would have written it differently, because taste
is not a defect.
</requesting_changes>
