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
complementary sources were linked to the core sections they had been deciding independently.

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
universality passes. Thirty-seven focused unit tests pass across instruction structure, authoring prose, evaluation
path resolution, context budget, single-home wording, the keyword-bag guard, negative-regex policy, and baseline
freshness. The evaluation baseline gate passes. A rebuild is green. The deployed core is byte-identical across Claude,
Codex, and OpenCode, and the generated core skills differ only by one appended newline from the generator. Hermes
receives canonical core through its managed soul file.

Pi reads core declaratively, but no host imports its module, so its deployment path is unexercised rather than
passing. It must not be counted as live evidence.

## The gap

No durable scenario proves that a core rule survives compaction. Every end-to-end scenario in the tree is a
single-session probe, and none references compaction at all. The only evidence of the required shape was one manual
run: a fresh session, several non-coding turns, a real native compaction, then an unprompted coding request whose
artifact came back comment-free with descriptive names and one responsibility. One run, one harness, never automated.

The evaluation and integration suites cannot close this. They establish short-term instruction following, which is why
the original regression stayed invisible to them.

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
copying policy into a fixture or adding a test-only prompt. Its assertions cover the observable contract that exposed
the original regression: no comments or docstrings, descriptive names, cohesive responsibility.

## How to continue

The authority half runs the post-migration audit across the core-rule documents, the skills and the chapters they route
to, the project-context policy files, and the four harness injection paths. Similarity alone never justifies a change;
each candidate gets a behavior contract and a runtime trace first. The guard and evidence files change only when the
audit confirms a migration, because they are guards, not the policy owner. Core grows only if the audit proves a
universal session-long behavior is missing.

The evidence half builds the durable post-compaction scenario. The scenario runner already accepts a list of prompts,
so the missing pieces are a compaction step between turns, enough prior non-coding turns for compaction to have
something to compact, and coverage through the real session mechanism of each supported harness rather than Claude
alone.

Completion is the intersection. The audit finds no competing or wrong-horizon authority, every confirmed complement
points to core, deployment parity holds, and the scenario demonstrates that the same canonical behavior survives
compaction in each live harness.
