# Wellput audit: evidence and limits

[Audit overview](../skill-audit.md). Reviewer: Gilgamesh. Snapshot date: 2026-10-18.

## Sources and scope

The main source is the canonical Humanize skill copied and renamed by [the exporter](../scripts/export_plugin.py). Public quotations use [Wellput 80aeb063](https://github.com/Castrozan/wellput/blob/80aeb06381904ed2952372cab8cf7b831d4bf782/skills/wellput/SKILL.md). The 68 stable body-sentence IDs and categories come from the [sentence review](../skill-review.md). YAML routing metadata is reviewed separately below.

The local norm is the supplied [instructions skill](../../skills/agent-workflows/instructions/SKILL.md), its [skill-writing](../../skills/agent-workflows/instructions/references/skills.md) and [refinement](../../skills/agent-workflows/instructions/references/refine.md) chapters, plus the repository's ownership, evidence, and completion principles. Current model quality is not inferred from conformance to Markdown grammar.

## Actual Stop-hook probes

All seven fixtures invoked the actual public `hooks/reply_hook.py` in a subprocess with `python3 -S`, event `Stop`, and direct `reply_text`. Bundled defaults were selected explicitly through `WELLPUT_CONFIG` to exclude user overrides. The package's vendored parser was therefore used without a new model call. Requests are listed to define the task contract; the production driver passes only the reply text to the rule catalog. Supplying request text in additional JSON fields did not change that path.

| #   | User request / fixture                                           | Submitted answer                                                                                | Observed decision                               | What this establishes                                                                                                                                                      |
| --- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Reply with exactly `Absolutely` and nothing else.                | `Absolutely`                                                                                    | Block: reaction opener.                         | The default has no exact-request exception for this literal.                                                                                                               |
| 2   | Return exactly a Markdown table with columns `Name` and `Value`. | A two-column `timeout`/`30` table.                                                              | Block: missing leading `#` column.              | The exact requested schema and the compulsory index disagree.                                                                                                              |
| 3   | Give the six recovery actions as a numbered list.                | Six numbered items: stop, capture depth, restore, start, wait ready, resume.                    | Block: six list lines exceed five.              | A natural answer to the existing semantic evaluation is rejected. It is possible to combine actions into fewer items, so this alone is not an impossibility proof.         |
| 4   | Return only a JSON object, with no Markdown or prose.            | An object with a string containing 120 `detail` words; the checker counts 121 whitespace words. | Block: missing required labels and body budget. | Labels or a code fence would change the requested raw JSON artifact.                                                                                                       |
| 5   | Explain a deployment result.                                     | An indexed one-row table whose explanation cell contains 250 `detail` words.                    | Accept.                                         | A mechanically valid table can still violate S19's semantic ban on disguising linear prose. This is an exclusion boundary, not an exploit requiring a new heuristic regex. |
| 6   | Did the check pass?                                              | `The check passed.`                                                                             | Accept.                                         | Short ordinary replies continue to work.                                                                                                                                   |
| 7   | Quote the release note exactly.                                  | `"Retries are bounded — the worker stops after attempt three."`                                 | Accept.                                         | The quoted-punctuation exception works; the audit does not claim that all exact source text is rejected.                                                                   |

### Why request precedence is not implemented here

[The hook driver](../assets/hooks/reply_hook.py) obtains `reply_text` or `last_assistant_message`, falling back to the final transcript reply. `stop_decision` then calls `template_violations_in_reply(reply)` with no task/request argument. [The catalog](../../../hooks/runtime/common/human_facing_reply/reply_rule_catalog.py) builds `ReplyUnderReview` from that text and configuration. No request-aware material exception is applied along this path.

The [configuration](../../../hooks/runtime/common/human_facing_reply/reply-formats.json) defines the opener patterns, table indexes, budgets, and list ceiling. [The violation functions](../../../hooks/runtime/common/human_facing_reply/reply_rule_violations.py) apply them. [Word-budget code](../../../hooks/runtime/common/human_facing_reply/reply_word_budget.py) correctly includes the configured grace; the audit does not mistake the nominal 100-word budget for an enforced 100-word hard threshold.

[Markdown parsing](../../../hooks/runtime/common/human_facing_reply/reply_markdown_document.py) excludes table, fenced-code, and other configured visual lines before [word metrics](../../../hooks/runtime/common/human_facing_reply/reply_text_metrics.py) are calculated. It validates structure, not whether the table communicates an actual mapping or relationship.

### Repair limits and preservation

The repair message asks for a fix to the existing reply and suggests moving suitable detail into excluded structures when over budget. That is not sufficient to arbitrate an exact output request against a mandatory structural rule. The word 'suitable' matters: the desired fix is not to make every long paragraph an uncounted table.

The `stop_hook_active` guard intentionally returns acceptance during an active Stop repair. The [portable verifier](../__tests__/portable/verify_plugin.py) tests that guard. Retain bounded repair behavior; removing the guard to promise unlimited enforcement would create a loop risk. The checker cannot establish semantic compliance merely by requesting one repair.

## Evaluation composition

The [current recovery suite](../../skills/writing/humanize/__tests__/evals/reader_recovery.yaml) has 22 authored cases, including three controls. It includes `channel_uses_numbered_steps_for_an_ordered_procedure`, whose rubric asks for all six actions in the supplied order. It does not require a separate item per action, which is why the six-item probe is a natural valid fixture rather than a proof that the rubric is impossible to satisfy.

The [subject runner](../../../quality/evaluations/runner/execution/run_evals_test_runner.py) invokes the model and passes its output to [authored assertions](../../../quality/evaluations/runner/judging/run_evals_assertions.py), including an LLM judge. That assertion path does not call the production reply-rule catalog. Hook test runners exist separately; their presence does not compose these semantic cases with Stop acceptance.

Useful existing controls are operational anger despite a clear explanation, preserved exact code identifiers, a successful diagram when relationships need it, and exact quoted punctuation. They disconfirm blanket advice such as 'anger means bad writing', 'remove all jargon', 'never use diagrams after confusion', or 'all em dashes must be removed'.

## Historical evidence is not current evidence

The [recorded baseline](../../../quality/evaluations/baseline.json) contains a checkpoint result dated 2026-10-05 with 21 passes and one failure across 22 recovery cases. The failed recorded case is `recovery_surfaces_the_requested_decision`. It is historical evidence from commit `4859a269c`, not a newly reproduced failure of today's skill.

The stored paired profile is dated 2026-08-23 and covers 21 cases over three epochs, or 63 paired samples. It reports a candidate/control pass-rate difference of 0.0317, with stored interval bounds 0.0 and 0.1111. That interval does not establish a strictly positive difference, and the profile is not for the current instruction fingerprints.

| #   | Component    | Recorded paired-profile fingerprint                                | Current fingerprint from the repository's helper                   |
| --- | ------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| 1   | Suite        | `7680eb17219f8525cedb6d77c999f02f72ade6397776bd1a639a8370d87c5772` | `ea265e8e0a830a9773f8bf33a2c443514d8bc138eff1d49ac70bd19b079efc28` |
| 2   | Instructions | `82e6e9d608ccd99b0d1e219e0e7d7aa2c8fa19bd6d5b686a040ab59c0f654f98` | `f12c684d1e2594d229b4bd394dcb4fda1eaa43e85a477bc5745a215aa351a7ce` |

Current fingerprints were computed with `humanize_recovery_fingerprints` from [the existing helper](../../../quality/evaluations/runner/baseline/run_evals_fingerprint.py). No model, judge, new baseline, or full test tier was run. The missing evidence is a current scoped comparison and composed runtime grading of candidate outputs.

### Literal-preservation blind spot in normalization

The same helper's `instruction_wording` removes Markdown emphasis/code delimiters and lowercases all instruction text. Two direct probes produce identical normalized wording for `Preserve contentCache exactly` versus `Preserve contentcache exactly`, and for `Return exactly DONE` versus `Return exactly done`, with the identifiers/outputs originally enclosed in inline code. These instructions specify different exact strings, so the equality is a fingerprint limitation rather than evidence of semantic equivalence.

This does not invalidate the current mismatch, which the helper does detect, or prove a model-output regression. It shows that future evidence accounting can miss case-only changes to exact literals. Preserve exact code/quotation spans during normalization, or use a conservative fingerprint where that distinction is material. This is an independent limit in F09, related to S9 and S39.

## Authoring mechanics

The existing instruction inspector reports no main-source Markdown/heading/paragraph violations and 14 anchors. The canonical file has 140 physical lines, no overlong body lines under the existing wrapper rule, and approximately 1,338 whitespace-separated body words across 22 prose paragraphs. These word counts are not tokenizer measurements. Long YAML values are exempt from prose wrapping.

[The export replacement](../scripts/export_plugin.py) changes the docs pointer to artifact writing without rewrapping the paragraph. The exported `SKILL.md` has a verified 154-character body line at line 133, past the local 120-character prose rule. Its heading/paragraph structure still passes. This is the sole mechanical authoring defect reported, and it is not evidence of a semantic model regression.

[The ownership tests](../../../quality/evaluations/__tests__/unit/instruction-policy/test_human_communication_policy_ownership.py) require the current section names and phrases for concrete choices, established language, and cohesion. [Representation tests](../../../quality/evaluations/__tests__/unit/interactive-policy/test_interactive_representation_policy.py) require the named mappings and anchor. These are useful migration guards, but matching their strings cannot prove comprehension or adherence.

## Routing metadata

The exported name matches `wellput`; the shared source remains `humanize`. The routing description covers substantial drafting and revision and exempts short confirmations and factual answers. Its role is discovery, not output-format validation. A sentence-based loading exemption and a word-based handoff threshold need not be identical because they serve different purposes.

The unresolved routing question is the meaning of 'substantial' for an important but short warning or explanation. Clarify that only if real selection cases fail; do not invent a universal word-count gate for skill loading. The body correctly avoids simply copying its frontmatter trigger. The larger local concern is that the body contains all bounded adaptations rather than a minimal entry with optional references.

## Delivery and scope

The actual SessionStart subprocess emitted 5,359 characters and approximately 796 whitespace words in the public checkout path used for the probe. Its output includes format rules, a fixed senior-engineer audience, and a requirement to publish local artifacts to an authorized remote. That establishes what the driver emits, not what every installed client receives.

The public [Core reference](https://github.com/Castrozan/wellput/blob/80aeb06381904ed2952372cab8cf7b831d4bf782/skills/wellput/references/core.md) includes implementation selection, testing, CI watching, and preservation of unrelated workspace work. The public [artifact-writing adapter](https://github.com/Castrozan/wellput/blob/80aeb06381904ed2952372cab8cf7b831d4bf782/skills/wellput/references/artifact-writing.md) restricts directory snapshots and when separate documents are written. These imports are broader than the writing semantics of S25 and S65.

Official [Codex hook documentation](https://learn.chatgpt.com/docs/hooks) says plugin hooks require trust and defines `additionalContextLimit` as an approximate token threshold. The configured value `5000` must not be compared with a 5,359-character output. That suspected truncation finding was discarded. This audit did not exercise a new installed Codex/Claude session, hook trust, or post-compaction delivery.

## How to read the conclusions

Blocked fixtures and current formatting deviations are reproduced facts. Duplicate wording, overlapping branches, and broad imports are source observations. Predicted over-explanation, poorer word choice, or reduced cognitive load are reasoned risks and recommendations requiring model comparison. A recommendation to remove a sentence is not a claim that deletion has already improved behavior.
