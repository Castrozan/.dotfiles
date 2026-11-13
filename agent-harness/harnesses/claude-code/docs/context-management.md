# Claude Code Context Management

Claude Code's context window depends on which model **variant** is selected: the bare model id is the 200K window, and the 1M window is a separate `/model` picker entry per 1M-capable model, shown as "(1M context)" and selected by the `[1m]` suffix (e.g. `opus[1m]`) or the picker's "Default" entry. The 1M window is therefore **not automatic** from the bare first-party id; you must select the `[1m]` variant. `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` forces any selection back to 200K. Older or non-first-party models are 200K only. The session model is runtime-owned (see Configuration below). Long sessions with heavy tool use, parallel subagents, and large file reads can exhaust the window, causing compaction (lossy summarization) or outright API failures on `--resume`. This document covers how context works, what breaks, and how to manage it.

## The Resume 500 Problem

When `claude --resume <session-id>` is called, Claude Code reconstructs the full raw conversation history from the `.jsonl` session file and sends it to the Anthropic API. If the session accumulated massive tool results (parallel subagent outputs of 300-400KB each, large file reads, hundreds of progress entries), the reconstructed payload exceeds what the API can handle. Instead of returning a proper 413 (payload too large), Anthropic's server returns a 500 internal server error. The session is not recoverable via resume.

Symptoms: `API Error: 500 {"type":"error","error":{"type":"api_error","message":"Internal server error"}}` immediately on resume. The session file itself is intact (typically 1000+ entries, several MB), but the API cannot process it. Autocompact may show reasonable token counts (~80K) because it tracks the live compacted state, not the raw history that resume reconstructs.

Prevention: aggressive compaction thresholds, smaller sessions, offloading heavy work to subagents (whose results can be summarized).

## Compaction

Auto-compaction triggers when token usage approaches the context window limit. It summarizes earlier conversation turns to free space. This is lossy — nuanced technical details, specific code snippets, and earlier decisions can be lost.

### Configuration

`CLAUDE_CODE_AUTO_COMPACT_WINDOW` sets the auto-compact base. In 2.1.321 the effective window is the smaller of the model's real window and that base (floored at 100K, capped at 1M), and the trigger is that window minus the output reserve and the summary buffer. `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` can only lower the trigger further, and because it is relative to the effective window it lands on a different absolute trigger for a 200K model than for a 1M one, so it stays unset. The blocking level is computed separately from the model's real window (`rtt` receives `But(model)`, the real window minus the output reserve, and blocks at that minus 3000), so a base below a `[1m]` model's window lowers only the trigger and keeps the rest of the 1M window as overshoot headroom. One absolute base therefore gives every session, 200K or 1M, interactive or clawde, the same lean trigger. `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` would force the real window back to 200K and is unset.

The base lives in `agent-harness/harnesses/claude-code/settings/environment-variables.nix`; read it for the live value, which is deliberately not copied here. The session model is runtime-owned: `model` stays in the mutable `settings.json` across rebuilds, the interactive `claude` wrapper passes no `--model`, and agents that need another model pass `--model` per launch. What drives output quality is context **fill**, not window **size**: the same weights and the same attention degrade as the *used* token count climbs, well before any ceiling and regardless of how large that ceiling is (Chroma's [Context Rot](https://research.trychroma.com/context-rot), Jul 2025; [NoLiMa](https://arxiv.org/abs/2502.05167), Feb 2025; Anthropic's [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), Sep 2025). Cost tracks fill too, because every turn re-reads the whole context from the prompt cache, so a session left to grow toward a 1M wall pays for its whole history on every request. The trigger is the lever for both; microcompaction offloads the stale tool-result tail between compactions.

The explicit window also fixes the display. The status-line label is chosen by `J = !Wo() && !Y5_(model, window)`, where `Y5_` is true when `Pc(model, window).source` is `env`, `settings`, or `model-default`. With nothing set the source resolves to `auto`, `Y5_` is false, `J` is true, and the line reads `${100−j}% context used` against the usable window (`c4H` ≈ real window minus reserved output) — so the percentage runs against the hard wall rather than the trigger. Setting `CLAUDE_CODE_AUTO_COMPACT_WINDOW` makes the source `env`, flips `J` false, and switches the line to the honest `${j}% until auto-compact`, a countdown that hits 0% at the compact trigger rather than at the hard wall. (`Wo` is unrelated — it gates on the `tengu_amber_redwood3` statsig experiment, not on any env var.)

Disabling auto-compaction entirely: `claude config set -g autoCompactEnabled false` writes to `~/.claude.json`. The setting in `~/.claude/settings.json` is silently ignored — this is a known gotcha. The `/config` toggle is per-session only.

Manual compaction with `/compact <what to preserve>` lets you control what survives. `/compact` without arguments uses defaults. The community-proposed `/compact-next <instructions>` (queuing compaction instructions without executing immediately) is not yet implemented.

Every compaction, automatic or manual, also carries a standing brief from the dotfiles plugin's `compaction-brief` hooks module under `agent-harness/harnesses/claude-code/plugins/mods/`: its `session.compact` hook appends the brief after any text typed after `/compact`. A settings-file `PreCompact` hook cannot do this, because it can only block a compaction, never change its instructions.

Idle compaction is native: the [`idleCompaction`](https://code.claude.com/docs/en/settings-reference#idlecompaction) setting, on by default, compacts a large interactive conversation shortly before its one-hour prompt cache expires. Its size threshold and timing are upstream's; read that page rather than copying them here. `CLAUDE_CODE_IDLE_COMPACT_MIN_TOKENS` sets the size it requires (upstream floor 100K). The upstream default sits above a 200K-based trigger, so `environment-variables.nix` lowers it; otherwise a session idle past the cache lifetime would never be idle-compacted and would rewrite its whole context into the cache on return.

### Strategies to Reduce Context Pressure

Subagents via the Task tool get their own context windows. Heavy exploration, file reads, and searches should be delegated to subagents, keeping the parent session lean. CLAUDE.md should contain short pointers to guide files on disk rather than inlining large blocks — Claude reads guides on-demand when the conversation triggers them.

## Extended Context (1M Token Window)

Every 1M-capable model opts into the 1M window via the `[1m]` suffix; the bare model id stays at 200K. The `/model` picker exposes a distinct "(1M context)" entry per 1M-capable first-party model, each selected by the suffixed id or alias:

```
/model opus[1m]              # alias, latest Opus at 1M
/model <exact-model-id>[1m]  # exact version pin at 1M
/model sonnet[1m]
```

The bare `opus` alias resolves to the non-1M everyday Opus, so it does not grant the 1M window; use the `[1m]` form. The picker's "Default" entry tracks whatever Anthropic sets as the recommended default and can shift under you, so pin the explicit `[1m]` id when the window must not drift.

### Plan Availability (as of June 2026)

The February-2026 restriction is gone. Since March 2026, Max, Team, and Enterprise plans can use the 1M window in Claude Code for Opus 4.8, Opus 4.7, Opus 4.6, and Fable 5 with no surcharge, but it stays opt-in per model via the `[1m]` variant rather than being applied automatically to the bare id. Pro users get the same models at 1M only after enabling usage credits. API and Claude Code pay-as-you-go users also have it. The old "NOT available on Max" claim and the tier-4-only gate no longer hold; the earlier disappear-after-update regressions are tracked in [#26428](https://github.com/anthropics/claude-code/issues/26428) and [#15057](https://github.com/anthropics/claude-code/issues/15057).

Pricing: Opus 4.x now serve the full 1M window at standard rates, so the old 2x-input / 1.5x-output surcharge above 200K no longer applies to these models. 1M is GA for them with no beta header and no surcharge, but it still requires selecting the `[1m]` variant; the bare id remains 200K. Turning the 1M window off (a bare id or `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`) is **not** itself an output-quality move: quality tracks context fill, not window size, so the quality lever is a low absolute auto-compact trigger (see Configuration) with the 1M window held as headroom rather than filled. A bare id only lowers the hard wall and buys no quality at equal fill.

## Model Switching

`/model <alias>` switches models mid-session without losing conversation history. The new model receives the full prior context. Available aliases: `default`, `sonnet`, `opus`, `haiku`, `opus[1m]`, `sonnet[1m]`, `opusplan`.

`opusplan` uses Opus for planning and auto-switches to Sonnet for execution — the only shipped form of autonomous model routing.

### What Doesn't Exist Yet

Autonomous model switching (Claude deciding to change models based on task complexity or context pressure) is not implemented. The most relevant open feature requests:

- [#23920](https://github.com/anthropics/claude-code/issues/23920) — Auto-upgrade to `[1m]` instead of compacting. Proposes `contextLimitAction: "upgrade"` setting.
- [#22206](https://github.com/anthropics/claude-code/issues/22206) — Programmatic model switching based on task complexity (set_model tool, MCP action, or auto-assessment).
- [#19269](https://github.com/anthropics/claude-code/issues/19269) — Per-tool model routing (Haiku for reads, Opus for architecture). Marked high-priority.
- [#15721](https://github.com/anthropics/claude-code/issues/15721) — Auto plan/execute model routing. Marked high-priority.

## Token Cost and Caching

Conversation-history re-read (`cache_read`) dominates token cost: every tool result and message is re-sent on each later turn until compaction or `/clear`, so a byte added once is re-billed on every subsequent turn. The levers are behavioral and live in `agent-harness/agent-instructions/core-rules/core.md` (`<context-budget>`, `<delegation>`, `<audience>`): keep the working set small, delegate heavy reads to subagents whose output never enters the parent history, and `/clear` at task boundaries. Deployed output caps (`MAX_MCP_OUTPUT_TOKENS`, `BASH_MAX_OUTPUT_LENGTH`) live in `environment-variables.nix`; read that file for the values.

Caching invariants worth not breaking: on a Claude subscription the 1-hour cache TTL is auto-requested for free, so never set `FORCE_PROMPT_CACHING_5M` (it shortens the TTL, expires warm prefixes, and drops the hit ratio). The cache key includes both model and effort, so switching either mid-session, or using the `opusplan` alias that toggles Opus and Sonnet, reprocesses the entire history uncached. Keeping MCP tools deferred via Tool Search means a server connecting or disconnecting only appends and leaves the cached prefix intact, so never force tools upfront or add an `alwaysLoad` exemption.

## Scrollback and Session History

Claude Code's fullscreen TUI renders on the terminal's alternate screen and uses DEC scroll-region escapes (DECSTBM), so streamed output never reaches the terminal's native scrollback; stripping alt-screen at the multiplexer does not stop the DECSTBM escapes. The durable record of a conversation is its session jsonl under `~/.claude/projects/<encoded-cwd>/`, reachable via `claude --resume <uuid>` or a direct `Read`. That file, not multiplexer scrollback, is where "search the whole session" or "grab text from much earlier" is answered, and it is independent of the multiplexer, so conversations from another window or a background agent are reachable the same way.

## References

- [Model Configuration](https://code.claude.com/docs/en/model-config)
- [Context Windows API Docs](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [Original 1M feature request #5644](https://github.com/anthropics/claude-code/issues/5644) (60+ comments)
- [Compaction API docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
