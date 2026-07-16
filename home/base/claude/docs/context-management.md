# Claude Code Context Management

Claude Code's context window depends on which model **variant** is selected, and the bare model id is the 200K variant. The live `/model` picker (claude-code 2.1.195) lists two Opus 4.8 entries: the bare id `claude-opus-4-8` shows "Opus 4.8" and is the **200K** window, while the 1M variant is a separate entry shown as "Opus 4.8 (1M context)" selected by the `[1m]` suffix (`claude-opus-4-8[1m]`, alias `opus[1m]`) or the picker's "Default" entry. The 1M window is therefore **not automatic** from the bare first-party id; you must select the `[1m]` variant. `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` forces any selection back to 200K. Older or non-first-party models are 200K only. This repo pins the 1M variant durably (see Configuration below). Long sessions with heavy tool use, parallel subagents, and large file reads can exhaust the window, causing compaction (lossy summarization) or outright API failures on `--resume`. This document covers how context works, what breaks, and how to manage it.

## The Resume 500 Problem

When `claude --resume <session-id>` is called, Claude Code reconstructs the full raw conversation history from the `.jsonl` session file and sends it to the Anthropic API. If the session accumulated massive tool results (parallel subagent outputs of 300-400KB each, large file reads, hundreds of progress entries), the reconstructed payload exceeds what the API can handle. Instead of returning a proper 413 (payload too large), Anthropic's server returns a 500 internal server error. The session is not recoverable via resume.

Symptoms: `API Error: 500 {"type":"error","error":{"type":"api_error","message":"Internal server error"}}` immediately on resume. The session file itself is intact (typically 1000+ entries, several MB), but the API cannot process it. Autocompact may show reasonable token counts (~80K) because it tracks the live compacted state, not the raw history that resume reconstructs.

Prevention: aggressive compaction thresholds, smaller sessions, offloading heavy work to subagents (whose results can be summarized).

## Compaction

Auto-compaction triggers when token usage approaches the context window limit. It summarizes earlier conversation turns to free space. This is lossy — nuanced technical details, specific code snippets, and earlier decisions can be lost.

### Configuration

`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` controls when compaction fires, as a percentage (1-100) of the **effective auto-compact window**, not of "context used". In the binary (`gu6`) the threshold is `min(window × pct/100, window − 13000)`. That window is the model's full context, so the percentage and the auto-compact base must describe the same window or the trigger lands somewhere nonsensical: leaving `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000` while the real model window is 1M would fire compaction at ~180K and waste the rest, while leaving the window at 1M but on a 200K model would never fire before the hard wall. `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` forces the real model window back to 200K, and `CLAUDE_CODE_AUTO_COMPACT_WINDOW=<tokens>` sets the auto-compact base explicitly (floored at 100K via `I3q`, capped at 1M via `QnK`, both validated by `X7H`). `CLAUDE_CODE_AUTO_COMPACT_WINDOW` and `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` live in `home/base/claude/settings/environment-variables.nix`; `CLAUDE_CODE_DISABLE_1M_CONTEXT` is the optional reversal toggle and is currently unset there.

The deployed config selects the 1M variant (`model = "claude-opus-4-8[1m]"` in `home/base/claude/settings/global-settings.nix`, and no `CLAUDE_CODE_DISABLE_1M_CONTEXT`) + `CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000` + `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=35`, giving a compact trigger of `gu6(1000000, 35) = min(350000, 987000) = 350000` tokens. The model selection is load-bearing for this math: the repo previously pinned the bare `claude-opus-4-8` id, which is the 200K variant, so the 1M auto-compact base never fired before the real 200K wall — the exact mismatch warned of one sentence up. Selecting the `[1m]` variant realigns the auto-compact base with the real window. The pin must live in `global-settings.nix` because `seed-claude-settings-mutable.sh` re-applies `model` from the nix-source on every rebuild (`model` is not in the runtime-preserved allowlist), so a manual `/model` switch does not survive a rebuild. This `settings.json` `model` is the default every session inherits, so it is deliberately held at `claude-opus-4-8[1m]` for the sessions that must keep it — clawde background agents, headless runs, subagents, and any other non-interactive launch. Interactive keyboard sessions set the model explicitly to `claude-opus-4-8[1m]` too: the `claude-workspace` launcher exports `CLAUDE_INTERACTIVE_MODEL` (in `skill-injection/interactive-workspace-sessions.nix`) and `launch-claude-workspace-session` turns it into a `--model` flag, which the CLI takes over the settings default; the same launcher scrubs that env var when the `CLAWDE_RESUME_FLAG` marker is present, so clawde background agents keep the settings default directly. Interactive and non-interactive sessions therefore run the same `claude-opus-4-8[1m]` variant, so the 350K auto-compact trigger and the blocking-level math above are identical across both. Setting the auto-compact base equal to the real 1M window aligns the blocking level — `pnK` computes it as `window − 3000 = 997000` — to the real API wall instead of pulling it down, so a heavy turn that overshoots the 350K trigger has ~647K of headroom before it can be falsely blocked. The 350K trigger is a deliberate low setting: it keeps the routine working set well inside the higher-signal regime where Opus attention stays sharp, while leaving real raw headroom for the occasional big single-context job (wide workflows, large surveys), with microcompaction offloading the stale-tool-result tail in between. It was lowered to 350K from an earlier 500K (itself down from an original 900K), each step trading raw window for answer quality as the routine working set stays smaller. To prioritize output quality further, drop `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` lower still (e.g. `20` for a 200K trigger) or re-add `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` and clamp to a 200K window (e.g. `200000` × `70` = 140K); to favor raw window for big single-context jobs, raise it back toward `90`. The trigger only fires before the real wall on a model whose actual window is ≥ the auto-compact base; a non-1M model under this config would hit the hard 200K wall before 350K.

The explicit window also fixes the display. The status-line label is chosen by `J = !Wo() && !Y5_(model, window)`, where `Y5_` is true when `Pc(model, window).source` is `env`, `settings`, or `model-default`. With nothing set the source resolves to `auto`, `Y5_` is false, `J` is true, and the line reads `${100−j}% context used` against the usable window (`c4H` ≈ real window minus reserved output) — so the percentage runs against the hard wall rather than the trigger. Setting `CLAUDE_CODE_AUTO_COMPACT_WINDOW` makes the source `env`, flips `J` false, and switches the line to the honest `${j}% until auto-compact`, a countdown that hits 0% at the 350K compact trigger rather than at the hard wall. (`Wo` is unrelated — it gates on the `tengu_amber_redwood3` statsig experiment, not on any env var.)

Disabling auto-compaction entirely: `claude config set -g autoCompactEnabled false` writes to `~/.claude.json`. The setting in `~/.claude/settings.json` is silently ignored — this is a known gotcha. The `/config` toggle is per-session only.

Manual compaction with `/compact <what to preserve>` lets you control what survives. `/compact` without arguments uses defaults. The community-proposed `/compact-next <instructions>` (queuing compaction instructions without executing immediately) is not yet implemented.

### Strategies to Reduce Context Pressure

Subagents via the Task tool get their own context windows. Heavy exploration, file reads, and searches should be delegated to subagents, keeping the parent session lean. CLAUDE.md should contain short pointers to guide files on disk rather than inlining large blocks — Claude reads guides on-demand when the conversation triggers them.

## Extended Context (1M Token Window)

Every 1M-capable model opts into the 1M window via the `[1m]` suffix; the bare model id stays at 200K. The `/model` picker exposes a distinct "(1M context)" entry per capable model (Opus 4.8/4.7/4.6, Sonnet 4.6/4.5, Fable 5), each selected by the suffixed id or alias:

```
/model opus[1m]              # alias, latest Opus at 1M
/model claude-opus-4-8[1m]   # exact version pin at 1M
/model sonnet[1m]
```

The bare `opus` alias resolves to the non-1M "everyday" Opus 4.8, so it does not grant the 1M window — use the `[1m]` form. The picker's "Default" entry currently maps to the 1M Opus 4.8 and displays "Opus 4.8 (1M context)", but it tracks whatever Anthropic sets as the recommended default, so pin the explicit `[1m]` id when the window must not drift.

### Plan Availability (as of June 2026)

The February-2026 restriction is gone. Since March 2026, Max, Team, and Enterprise plans can use the 1M window in Claude Code for Opus 4.8, Opus 4.7, Opus 4.6, and Fable 5 with no surcharge, but it stays opt-in per model via the `[1m]` variant rather than being applied automatically to the bare id. Pro users get the same models at 1M only after enabling usage credits. API and Claude Code pay-as-you-go users also have it. The old "NOT available on Max" claim and the tier-4-only gate no longer hold; the earlier disappear-after-update regressions are tracked in [#26428](https://github.com/anthropics/claude-code/issues/26428) and [#15057](https://github.com/anthropics/claude-code/issues/15057).

Pricing: Opus 4.x now serve the full 1M window at standard rates, so the old 2x-input / 1.5x-output surcharge above 200K no longer applies to these models. 1M is GA for them with no beta header and no surcharge, but it still requires selecting the `[1m]` variant; the bare id remains 200K. To turn the 1M window OFF (the output-quality-first reversal described under Configuration), select a bare (non-`[1m]`) id or set `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`.

## Model Switching

`/model <alias>` switches models mid-session without losing conversation history. The new model receives the full prior context. Available aliases: `default`, `sonnet`, `opus`, `haiku`, `opus[1m]`, `sonnet[1m]`, `opusplan`.

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
