<philosophy>
You own testing. Never delegate verification to the user and never present untested code as complete. Verification
proves the behavior it actually exercises, not every theory used to reach the change: a green regression test is
evidence that the represented regression no longer occurs, not independent proof that the proposed root cause was
correct. When the environment prevents meaningful verification, state the exact missing evidence rather than converting
an untested claim into certainty.
</philosophy>

<before-changes>
For a bug, first establish a focused reproducer that fails for the reported behavior and, where practical, traverses the
same causal path; a test that merely resembles the symptom does not prove the diagnosis. For new behavior, define the
smallest focused testable contract before implementation. Read the relevant existing tests and use the narrowest
reproduction or probe that can distinguish the favored explanation from plausible alternatives.
</before-changes>

<coverage>
Cover the boundaries the changed behavior actually exposes: empty, malformed, duplicate, repeated, concurrent, or
failure inputs when those states are meaningful; every caller of a changed public signature; and the failure paths the
happy path skips. Do not manufacture irrelevant cases to satisfy a checklist. Repository tests own recurring regression
coverage so future agents do not have to rediscover it from prose.
</coverage>

<after-changes>
Run the focused reproducer first, then the repository's relevant build, static checks, integration tests, runtime
probes, or broader CI gate in the order that gives useful failure locality. Treat contradictory runtime or production
evidence as stronger than a green test that modeled the wrong thing. Diagnose flaky or state-dependent failures rather
than rerunning until green. Fix failures caused by the change and re-run the evidence that originally failed.
</after-changes>

<pre-delivery>
Before presenting results, re-read the user's actual request, compare the implementation against every material
requirement, verify that no unintended scope was added, and inspect the final artifact or behavior rather than relying
on an implementer's summary. Follow the repository's own instructions for full-suite, CI, deployment, and live-runtime
gates; do not copy one repository's delivery mechanics into this generic skill.
</pre-delivery>
