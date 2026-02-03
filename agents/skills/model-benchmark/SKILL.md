# Model Benchmark Skill

Benchmark OpenClaw models (Opus, Sonnet, Codex, Kimi) for performance comparison.

## Usage

```bash
cd ~/openclaw/projects/model-benchmark-$(date +%Y-%m-%d)
```

Or spawn benchmark sessions directly.

## Task Template

Write a Python script that:
1. Parses systemd journal logs via `journalctl` command
2. Extracts error patterns grouped by service
3. Generates summary report (JSON + markdown)
4. POSTs to webhook URL
5. Includes: argparse, error handling, dry-run mode
6. Output: Complete Python file at `log_analyzer.py`

## Metrics to Report

- Start/end timestamps
- Wall-clock duration
- Final code present in response
- Self-test: did it run `python -m py_compile`?
- Tool calls used

## Model Variants

| Session | Model | Purpose |
|---------|-------|---------|
| benchmark-opus | anthropic/claude-opus-4-5 | Premium quality |
| benchmark-sonnet | anthropic/claude-sonnet-4-5 | Fast quality |
| benchmark-codex | openai-codex/gpt-5.2-codex | Prod default |
| benchmark-kimi | nvidia/moonshotai/kimi-k2.5 | Free tier |

## Benchmark Results (2026-02-03)

Task: Write systemd journal log analyzer with JSON/md reports, webhook POST, argparse, dry-run, error handling.

| Model | Wall Time | Lines | py_compile | Verdict |
|-------|-----------|-------|------------|---------|
| **Opus** | 4s | 550 | ✓ PASS | Fastest, most comprehensive |
| **Sonnet** | 67s | 465 | ✓ PASS | Best balance quality/structure |
| **Codex** | 70s | 201 | ✓ PASS | Concise, modern Python |
| **Kimi** | ~105s | 247 | ✓ PASS | Free tier, reliable but slower |

### Recommendations for OpenClaw

| Use Case | Best Model | Why |
|----------|-----------|-----|
| Complex scripting | Opus | Fastest, production-ready output |
| Daily coding | Sonnet | Well-balanced, type hints, good structure |
| Speed/cost | Codex | Current default, concise, modern Python |
| Free tier | Kimi | Reliable, works on NVIDIA NIM (free) |
| Heartbeat | Kimi | Acceptable for free tier background tasks |
| Subagents | Sonnet | Fast + good quality for parallel work |
| Budget mode | Kimi | Completely free via NVIDIA NIM |

### File Locations

Benchmark outputs: `~/openclaw/projects/model-benchmark-2026-02-03/`
- `opus/log_analyzer.py` (550 lines)
- `sonnet/log_analyzer.py` (465 lines)
- `codex/log_analyzer.py` (201 lines)
- `kimi/log_analyzer.py` (247 lines)
- `benchmark_report.md` (full report)
