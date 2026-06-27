# Claude Code Context Management

Claude Code's context window depends on the model. On first-party `api.anthropic.com`, the current Claude 4.x models (opus-4-8, opus-4-7, fable-5, mythos-5) default to a **1M token window** with no `[1m]` suffix required; set `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` to fall back to the 200K window. Older or non-first-party models use 200K. Long sessions with heavy tool use, parallel subagents, and large file reads can exhaust this window, causing compaction (lossy summarization) or outright API failures on `--resume`. This document covers how context works, what breaks, and how to manage it.

## The Resume 500 Problem

When `claude --resume <session-id>` is called, Claude Code reconstructs the full raw conversation history from the `.jsonl` session file and sends it to the Anthropic API. If the session accumulated massive tool results (parallel subagent outputs of 300-400KB each, large file reads, hundreds of progress entries), the reconstructed payload exceeds what the API can handle. Instead of returning a proper 413 (payload too large), Anthropic's server returns a 500 internal server error. The session is not recoverable via resume.

Symptoms: `API Error: 500 {"type":"error","error":{"type":"api_error","message":"Internal server error"}}` immediately on resume. The session file itself is intact (typically 1000+ entries, several MB), but the API cannot process it. Autocompact may show reasonable token counts (~80K) because it tracks the live compacted state, not the raw history that resume reconstructs.

Prevention: aggressive compaction thresholds, smaller sessions, offloading heavy work to subagents (whose results can be summarized).

## Compaction

Auto-compaction triggers when token usage approaches the context window limit. It summarizes earlier conversation turns to free space. This is lossy — nuanced technical details, specific code snippets, and earlier decisions can be lost.

### Configuration

`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` controls when compaction fires, as a percentage (1-100) of the **effective auto-compact window**, not of "context used". In the binary (`gu6`) the threshold is `min(window × pct/100, window − 13000)`. That window is the model's full context, so the percentage and the auto-compact base must describe the same window or the trigger lands somewhere nonsensical: leaving `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000` while the real model window is 1M would fire compaction at ~180K and waste the rest, while leaving the window at 1M but on a 200K model would never fire before the hard wall. `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` forces the real model window back to 200K, and `CLAUDE_CODE_AUTO_COMPACT_WINDOW=<tokens>` sets the auto-compact base explicitly (floored at 100K via `I3q`, capped at 1M via `QnK`, both validated by `X7H`). `CLAUDE_CODE_AUTO_COMPACT_WINDOW` and `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` live in `home/base/claude/settings/environment-variables.nix`; `CLAUDE_CODE_DISABLE_1M_CONTEXT` is the optional reversal toggle and is currently unset there.

The deployed config is the native 1M window (no `CLAUDE_CODE_DISABLE_1M_CONTEXT`, so opus-4-8 keeps its first-party 1M default) + `CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000` + `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=90`, giving a compact trigger of `gu6(1000000, 90) = min(900000, 987000) = 900000` tokens. Setting the auto-compact base equal to the real 1M window aligns the blocking level — `pnK` computes it as `window − 3000 = 997000` — to the real API wall instead of pulling it down, so a heavy turn that overshoots the 900K trigger has ~97K of headroom before it can be falsely blocked. This trades Opus output quality for raw window: 900K is far past the point where output degrades, so it suits big single-context jobs (wide workflows, large surveys) and relies on microcompaction to offload the stale-tool-result tail in between. To prioritize output quality instead, re-add `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` and drop the window+percentage back to a 200K-clamped trigger (e.g. `200000` × `70` = 140K). The trigger only fires before the real wall on a model whose actual window is ≥ the auto-compact base; a non-1M model under this config would hit the hard 200K wall before 900K.

The explicit window also fixes the display. The status-line label is chosen by `J = !Wo() && !Y5_(model, window)`, where `Y5_` is true when `Pc(model, window).source` is `env`, `settings`, or `model-default`. With nothing set the source resolves to `auto`, `Y5_` is false, `J` is true, and the line reads `${100−j}% context used` against the usable window (`c4H` ≈ real window minus reserved output) — so the percentage runs against the hard wall rather than the trigger. Setting `CLAUDE_CODE_AUTO_COMPACT_WINDOW` makes the source `env`, flips `J` false, and switches the line to the honest `${j}% until auto-compact`, a countdown that hits 0% at the 900K compact trigger rather than at the hard wall. (`Wo` is unrelated — it gates on the `tengu_amber_redwood3` statsig experiment, not on any env var.)

Disabling auto-compaction entirely: `claude config set -g autoCompactEnabled false` writes to `~/.claude.json`. The setting in `~/.claude/settings.json` is silently ignored — this is a known gotcha. The `/config` toggle is per-session only.

Manual compaction with `/compact <what to preserve>` lets you control what survives. `/compact` without arguments uses defaults. The community-proposed `/compact-next <instructions>` (queuing compaction instructions without executing immediately) is not yet implemented.

### Strategies to Reduce Context Pressure

Subagents via the Task tool get their own context windows. Heavy exploration, file reads, and searches should be delegated to subagents, keeping the parent session lean. CLAUDE.md should contain short pointers to guide files on disk rather than inlining large blocks — Claude reads guides on-demand when the conversation triggers them.

## Extended Context (1M Token Window)

The current first-party Claude 4.x models (opus-4-8, opus-4-7, fable-5, mythos-5) enable the 1M window automatically on `api.anthropic.com` with no suffix needed (binary: `Im()` returns 1M for these when the platform is firstParty/Bedrock/mantle). Other 1M-capable models opt in via the `[1m]` suffix:

```
/model sonnet[1m]
/model opus[1m]
```

### Plan Availability (as of June 2026)

The February-2026 restriction is gone. Since March 2026, Max, Team, and Enterprise plans get the 1M window automatically in Claude Code for Opus 4.8, Opus 4.7, Opus 4.6, and Fable 5, with no surcharge and no configuration. Pro users get the same models at 1M only after enabling usage credits. API and Claude Code pay-as-you-go users also have it. The old "NOT available on Max" claim and the tier-4-only gate no longer hold; the earlier disappear-after-update regressions are tracked in [#26428](https://github.com/anthropics/claude-code/issues/26428) and [#15057](https://github.com/anthropics/claude-code/issues/15057).

Pricing: Opus 4.x now serve the full 1M window at standard rates, so the old 2x-input / 1.5x-output surcharge above 200K no longer applies to these models. 1M is GA for them with no `[1m]` suffix and no beta header; other models still opt in via `[1m]`. To turn the 1M window OFF (the output-quality-first reversal described under Configuration), set `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`.

## Model Switching

`/model <alias>` switches models mid-session without losing conversation history. The new model receives the full prior context. Available aliases: `default`, `sonnet`, `opus`, `haiku`, `sonnet[1m]`, `opusplan`.

`opusplan` uses Opus for planning and auto-switches to Sonnet for execution — the only shipped form of autonomous model routing.

### What Doesn't Exist Yet

Autonomous model switching (Claude deciding to change models based on task complexity or context pressure) is not implemented. The most relevant open feature requests:

- [#23920](https://github.com/anthropics/claude-code/issues/23920) — Auto-upgrade to `[1m]` instead of compacting. Proposes `contextLimitAction: "upgrade"` setting.
- [#22206](https://github.com/anthropics/claude-code/issues/22206) — Programmatic model switching based on task complexity (set_model tool, MCP action, or auto-assessment).
- [#19269](https://github.com/anthropics/claude-code/issues/19269) — Per-tool model routing (Haiku for reads, Opus for architecture). Marked high-priority.
- [#15721](https://github.com/anthropics/claude-code/issues/15721) — Auto plan/execute model routing. Marked high-priority.

## References

- [Model Configuration](https://code.claude.com/docs/en/model-config)
- [Context Windows API Docs](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [Original 1M feature request #5644](https://github.com/anthropics/claude-code/issues/5644) (60+ comments)
- [Compaction API docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
