# Instruction authority: what was built and what remains

## Goal

A rule that must govern a whole session cannot live only in an on-demand skill. It disappears when the skill unloads,
it disappears after compaction, and slightly different copies of it in several surfaces disagree. That defect class
produced the visible regression: agents started writing comments and docstrings again once the no-comments rule left
the always-on surface.

The work removes the defect class rather than restoring the old maximal core. Authority is placed by scope and
lifetime. Core owns universal session-long behavior, including behavior triggered only while coding. Repository and
path context own local policy. Harness surfaces own delivery and mechanics. Skills own procedures bounded to one
operation. Hooks, permissions, CI, and operating-system controls own only predicates precise enough to enforce.
Complementary sources point to the canonical owner instead of restating it.

## Two halves, two questions

The work splits into two questions that do not substitute for each other.

Authority asks where a behavior belongs and whether every runtime receives one canonical version of it. Evidence asks
whether an ordinary agent still obeys that version after a session has aged and compacted. A perfect source audit
cannot claim long-session adherence, and a green end-to-end run cannot excuse duplicate authority.

## Built: the canonical core

`agent-harness/agent-instructions/core-rules/core.md` was rewritten as seven sections: evidence, autonomy, completion,
delegation, context, coding, and instruction-placement. Each rule states a trigger, an action, and its material
exceptions, so it determines behavior without inference.

The no-comments rule sits first inside `<coding>` with all four parts explicit: the trigger is creating or changing
owned code; the action forbids comments, docstrings, section banners, commented-out code, and TODO or FIXME notes; the
existing-state clause preserves current comments without treating them as permission to add more; the boundary excludes
generated and vendored code and required syntax directives.

Five skills stopped stating coding policy and started routing to core: `skills/coding/SKILL.md`,
`skills/coding/testing.md`, `skills/docs/SKILL.md`, `skills/architecture/SKILL.md`, and
`skills/agent-harness/SKILL.md`.

Guards followed. `agent-instructions/__tests__/checks.nix` requires the seven sections and rejects retired skill-only
ownership wording. `test_wording_rules_have_exactly_one_home.py` asserts core is the single no-comments authority and
that the full rule does not return to the migrated skills. The always-on instruction surface stays under its byte
ceiling. The `no_comments_principle` evaluation moved to core and its prompt became an ordinary coding request that
never names comments, so it measures adherence instead of recall.

Deliberate deviation: core carries no YAML frontmatter. Metadata moved to the harness boundaries that need it, and
Cursor keeps its own wrapper on `.cursor/rules/core.mdc` because its recognized surface requires metadata. One
harness's file format no longer contaminates the cross-harness policy source.

## Built: authority beyond core

The core rewrite was the first repaired instance, not the whole defect. The active instruction paths were audited and
each complementary source was linked to the core section that owns its behavior. Only some of them had been deciding
that behavior independently; the rest were already bounded complements that simply lacked an explicit pointer to core.

`skills/agent-harness/instruction-authority.md` is the reusable procedure that came out of it. It is a routed chapter,
not another always-on policy source, and it runs in six stages: state the behavior contract before comparing text;
trace the declared source through generated copies, deployment edges, prompt tiers, session caches, resume and
compaction behavior, and mutable state; select the owner only after that trace; classify every related surface as
canonical authority, generated copy, linked complement, deterministic control, behavioral evidence, historical
evidence, or competing authority; establish the new authority and its live delivery before deleting the old one; and
prove uniqueness, deployment equality, live injection, and the required horizon independently.

It blocks three recurring mistakes: moving every repeated sentence into core, treating exact enforcement as a
substitute for policy, and declaring a migration complete from source shape without proving runtime delivery.

The linked surfaces now include the adaptive implementation process, subagent briefs, Deep Work, Explore, Deliver,
Orchestrate, Research, Review, and Humanize. Each kept its bounded procedure.

One lesson is recorded in the work itself: removing duplicate authority is not the same as deleting useful scoped
procedure. Compressing Humanize too far while adding core pointers measurably lowered its reader-recovery quality, and
restoring the concrete supplied-fact procedure and the concrete human-facing distinctions recovered it. The core
pointer and the bounded contract must coexist.

Test design received the same treatment. A negative assertion that names bare tokens grades vocabulary rather than
behavior, so a policy module now rejects bare-token alternatives in negative regular expressions while allowing
structural patterns.

## Verified

Core sits at 4,661 bytes against a 5,000-byte guard with no line over 120 characters. The Nix check for core
universality passes. The focused unit suites pass across instruction structure, authoring prose, evaluation path
resolution, context budget, single-home wording, the keyword-bag guard, negative-regex policy, and baseline freshness.
The evaluation baseline gate passes. A rebuild is green. The deployed core is byte-identical across Claude, Codex, and
OpenCode, and the generated core skills differ only by one appended newline from the generator. Hermes receives
canonical core through its managed soul file.

The post-migration audit that closed the authority half found nothing left to migrate. Every surviving related source
is a generated copy, scoped repository policy, harness mechanics, or a bounded complement that names the core section
owning its behavior. The complete no-comments contract occurs in one file.

Pi reads core declaratively, but no host imports its module, so its deployment path is unexercised rather than
passing. It must not be counted as live evidence.

## The gap, and what closed it

The gap was that no durable scenario proved a core rule survives compaction. Every end-to-end scenario was a
single-session probe, and none referenced compaction. The only evidence of the required shape was one manual run, never
automated. The evaluation and integration suites cannot close this, because they establish short-term instruction
following, which is why the original regression stayed invisible to them.

Three automated scenarios now close it for three harnesses. Each drives a live session through six non-coding turns, a
real native compaction, and then an unprompted coding request, and grades the artifact rather than the transcript. All
three pass with the file changed and no comment written into it. The first runs were graded by the earlier substring
checker, so they established that no hash comment was written, not that no docstring was. The grader was rewritten
afterwards to parse the artifact instead, and every scenario has since run under it: Claude in roughly ten minutes,
Codex in roughly five, OpenCode in two and a half. Each artifact carries no comment, no docstring, and descriptive
names.

The compaction is not assumed in any of them. The step fails and the scenario stops before the coding turn unless the
harness prints its confirmation, so reaching the artifact at all is what proves the session was compacted. Claude and
Codex also leave that marker in the saved capture. OpenCode redraws inside the alternate screen, so its capture holds
only the closing frame and its confirmation has to be read live.

Compaction is driven per harness rather than by one guessed command. A harness earns a profile only after a live probe
records six facts: its manual compaction trigger, the marker it prints on success, the marker it prints when it
declines, the marker it shows while a turn is in flight, whether it blocks on a startup dialog in a fresh workspace and
how to launch past it, and whether Enter submits typed text or selects a highlighted dialog or palette entry. Every one
of those facts came from a failure that a guess would have hidden.

OpenCode 1.18.18 was recorded as failing the confirmation fact, and that verdict was wrong. The probe behind it spelled
the chord in tmux style, which the multiplexer rejects outright, so the keystroke never reached the application and the
harness was judged on a compaction it never performed. Driven with the spelling the multiplexer accepts, it compacts and
says so twice over: it prints a completion line carrying the model and an elapsed time, which cannot exist before the
work finishes, and its status bar drops from the pre-compaction context size to almost nothing before the summary is
written back. It has no refusal marker, so a request that never starts looks like one still running, and the absent
completion line after a timeout is what has to carry that case. On a session holding no message the trigger is inert and
its second key lands in the composer, so the first turn must clear it. It is now the third profiled harness and its
scenario passes.

## How the halves meet

The trace both halves share:

```text
canonical behavior contract in core.md
  -> harness-specific deployment edge
  -> live session prompt before and after native compaction
  -> ordinary request that never names the rule
  -> inspected artifact and trajectory
```

The audit supplies the canonical behaviors and the real deployment edges. The scenario consumes those edges rather than
copying policy into a fixture or adding a test-only prompt. Its assertions cover two of the three observable behaviors
that exposed the original regression. Comments and docstrings are graded by tokenizing and parsing the artifact, so a
docstring fails, a comment written without a following space fails, and a hash inside a string literal does not. Naming
is graded from the identifiers the artifact binds, so a single character fails, and so does any word inside a compound
name that matches a closed set of vowel-dropped forms with no standalone meaning. A name written only in underscores is
a discard and names nothing, and a name the runtime supplies by spelling, such as a test fixture, was never the author's
to pick, so neither is judged.

Cohesive responsibility stays ungraded on purpose. Every mechanical proxy considered, a statement ceiling and a
conjunction inside a function name among them, fails on domain terms no grader can enumerate, so it would reject correct
code. This repository puts a rule in a deterministic check only when its predicate and its material exceptions are
precise, so cohesion stays an instruction that a reviewer judges.

## How to continue

The authority half is closed. It reopens only if a new instruction source starts deciding universal session-long
behavior on its own, and any such claim needs a behavior contract and a runtime trace before an edit, because
similarity alone never justifies one. Core grows only when a universal session-long behavior is proven missing.

The evidence half is closed. OpenCode was its last open item, and the compaction it needed has now been watched on a
funded provider. Three consequences of that run are already in the tier. A harness driven by a key sequence needs its
profile to carry that sequence ahead of the typed directive. Its first turn must clear the composer, because the
trigger's second key lands there on a session holding no message. And OpenCode resolves its model from its own
configuration and ignores the configuration environment variable while the interface is running, so a scenario names
the model it needs and the launch command passes it through the one flag that harness honours.

Pi stays an unexercised declarative edge until a host imports its module.

Completion is the intersection. Nothing competes with core for authority, every confirmed complement points to it,
deployment parity holds, and the canonical behavior is shown to survive compaction in Claude, Codex, and OpenCode under
the current grader.
