### Question and tool

Use this to find where Claude Code tokens go and to test a compaction threshold against real sessions. Run
`scripts/transcript_token_analysis/main.py` from this skill with `summary`, `tools` or `replay`, plus `--days N` and
`--current-threshold N`; the defaults are 14 days and 400000.

Run it through a read-only `explore` subagent and ask for the three outputs condensed. The transcript tree is gigabytes
on this fleet, so only the report belongs in the parent context.

### Method

Read the usage Claude Code stores on each assistant line of `~/.claude/projects/*/*.jsonl`, the approach of
[ccusage](https://npmjs.com/package/ccusage). Weight tokens by relative price: cache read 0.1, five-minute cache write
1.25, one-hour cache write 2, output 5, fresh input 1. The weights give shape, not money; the usage collector's ledger
owns priced totals.

`summary` reports cost mix, cost by session length, turn-one context as the preamble proxy, cache reads per model and
top projects. `tools` reports tool result text and image bytes per tool, and Reads of a file already read in the same
session. `replay` re-runs each session's context growth under several compaction thresholds and reports compactions and
relative cost.

### Replay validation

Validate a replay before trusting it: at the live threshold it must reproduce the observed `compact_boundary` count. On
2026-11-27 it gave 32 replayed against 33 observed.

### Transcript duplication traps

An assistant message is written once per content block, so its usage repeats; keep the last usage per message id. About
15% of `tool_result` ids repeat across lines; count each id once. Summing raw lines overcounts both.

### Measurement limits

Image tool results are base64 in the transcript, so their bytes overstate their tokens. The system prompt and built-in
tool schemas are not recorded, so turn-one context includes them while the `attachment` lines (`skill_listing`,
`instructions`, `agent_listing_delta`, `deferred_tools_delta`) size only the remainder. Models differ in price, so the
weights compare shapes within a model and do not add up across models.

### Baseline

On 2026-11-27 over 14 days, 96 sessions and 16.6k turns, cost was 71% cache read, 17% cache write and 11% output. The 10
sessions over 500 turns carried 58% of cost, and context averaged 128k tokens per turn. Turn one held a median 29k
tokens, 21% of all context tokens. Fable and Opus held 75% of cache reads. Reads of an already-read file were 129 of
800, and Read bytes were 97% image.

Replay relative cost by trigger was 100% at 400k, 74% at 200k, 68% at 150k, 64% at 100k, 68% at 75k and 119% at 50k.
Compactions per 1000 turns were 1.9, 5.0, 7.5, 14.6, 25.9 and 106.4. Cost stops improving near 100k and compaction churn
dominates by 50k.

### Decision

The trigger was set to 200k with `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=20` on the 1M window, keeping the 1M window as
headroom as `agent-harness/harnesses/claude-code/docs/context-management.md` records.

### Reduction levers

By measured weight: bound session length through the compaction trigger and task-boundary checkpoints; route mechanical
work from Fable and Opus to cheaper models; downscale screenshots before Read; trim the preamble last, since cutting 6k
of 29k tokens saves about 4% in total.
