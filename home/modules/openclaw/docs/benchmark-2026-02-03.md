# OpenClaw Model Benchmark — 2026-02-03

**Permalink:** https://github.com/Castrozan/.dotfiles/blob/main/home/modules/openclaw/docs/benchmark-2026-02-03.md

## Goal
Compare four OpenClaw models (Opus 4.5, Sonnet 4.5, GPT-5.2-codex, Kimi k2.5) on the same engineering task to measure speed, output quality, and reliability.

## Test Procedure
1. Created a dedicated project directory:
   `~/openclaw/projects/model-benchmark-2026-02-03/` (archive: [docs/benchmarks/model-benchmark-2026-02-03](https://github.com/Castrozan/.dotfiles/tree/main/home/modules/openclaw/docs/benchmarks/model-benchmark-2026-02-03))
2. Ran **the same task prompt** against four separate model sessions (Opus, Sonnet, Codex, Kimi).
3. Each model was required to:
   - Write a complete Python script at `log_analyzer.py`
   - Use `journalctl` to parse systemd logs
   - Group error patterns by service
   - Output JSON + Markdown reports
   - POST to a webhook URL
   - Provide CLI args via argparse
   - Support dry-run
   - Include error handling
4. For each model we collected:
   - Start timestamp
   - End timestamp
   - Wall time
   - Line count of generated script
   - Whether `python -m py_compile` passed
   - Tool calls used
5. Final outputs were saved under:
   `~/openclaw/projects/model-benchmark-2026-02-03/{opus,sonnet,codex,kimi}/log_analyzer.py`
   - [Opus log_analyzer.py](https://github.com/Castrozan/.dotfiles/blob/main/home/modules/openclaw/docs/benchmarks/model-benchmark-2026-02-03/opus/log_analyzer.py)
   - [Sonnet log_analyzer.py](https://github.com/Castrozan/.dotfiles/blob/main/home/modules/openclaw/docs/benchmarks/model-benchmark-2026-02-03/sonnet/log_analyzer.py)
   - [Codex log_analyzer.py](https://github.com/Castrozan/.dotfiles/blob/main/home/modules/openclaw/docs/benchmarks/model-benchmark-2026-02-03/codex/log_analyzer.py)
   - [Kimi log_analyzer.py](https://github.com/Castrozan/.dotfiles/blob/main/home/modules/openclaw/docs/benchmarks/model-benchmark-2026-02-03/kimi/log_analyzer.py)

## Results
| Model | Cost per 1M (In/Out) | Time | Lines | Verdict | Ref. Fonte |
|------|----------------------|------|-------|---------|------------|
| Opus 4.5 | $5.00 / $25.00 | 4s | 550 | Fastest, most comprehensive | Anthropic |
| Sonnet 4.5 | $3.00 / $15.00 | 67s | 465 | Best balance quality/structure | Claude API |
| GPT-5.2-codex | $1.75 / $14.00 | 70s | 201 | Concise, modern Python | OpenAI API |
| Kimi k2.5 | $0.58 / $3.00* | ~120s | 247 | Best ROI, reliable subagent | Moonshot |

## Recommendations for OpenClaw
- **Primary:** GPT-5.2-codex or Opus 4.5 (cost-dependent)
- **Subagents:** Sonnet 4.5
- **Heartbeat:** Kimi k2.5 (free)
- **Budget mode:** Kimi k2.5 via NVIDIA NIM

## How the “model-benchmark” Skill Works
**Location:** `~/.dotfiles/agents/skills/model-benchmark/SKILL.md` ([link](https://github.com/Castrozan/.dotfiles/blob/main/agents/skills/model-benchmark/SKILL.md))

The skill standardizes the benchmark to keep models comparable:
- Provides a fixed **task template** (the journal log analyzer) so each model solves the same problem.
- Defines **metrics to report** (start/end time, wall time, py_compile, tool calls, code pasted).
- Lists **model variants** with exact model IDs to run (Opus, Sonnet, Codex, Kimi).
- Stores outputs in a predictable directory layout under `~/openclaw/projects/model-benchmark-YYYY-MM-DD/`.

This ensures every run is reproducible, and results can be compared directly without changing the prompt or evaluation criteria.
