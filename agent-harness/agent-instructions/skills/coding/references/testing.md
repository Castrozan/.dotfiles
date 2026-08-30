<core_verification_authority>
Core `<coding>` owns the persistent defaults for causal reproduction and claims bounded by evidence. This chapter owns
focused-before-broad execution order and flaky-failure diagnosis. Use it for the bounded testing procedure;
repository-local instructions may add stronger gates.
</core_verification_authority>

<before_changes>
For a bug, first create a focused reproducer that fails for the reported behavior and, where practical, traverses the
same causal path; a test that merely resembles the symptom cannot distinguish the diagnosis. For new behavior, define
the smallest focused testable contract before implementation. Read the relevant existing tests and use the narrowest
probe that can distinguish the favored explanation from plausible alternatives.
</before_changes>

<coverage>
Cover only meaningful boundaries exposed by the change: empty, malformed, duplicate, repeated, concurrent, or failure
inputs; every caller of a changed public signature; and failure paths skipped by the happy path. Repository tests own
recurring regression coverage so future work does not have to rediscover it from prose.
</coverage>

<execution>
Run the focused reproducer first, then the relevant build, static checks, integration tests, runtime probes, or broader
gate in the order that gives useful failure locality. Treat contradictory runtime evidence as stronger than a green test
that modeled the wrong behavior. Diagnose flaky or state-dependent failures instead of rerunning until green, fix
failures caused by the change, and rerun the evidence that originally failed.
</execution>

<repository_gates>
Follow the repository's own instructions for full-suite, CI, deployment, and live-runtime gates. Keep those mechanics in
the repository that owns them rather than copying them into this generic procedure.
</repository_gates>
