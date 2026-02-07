# Model Benchmark Skill

Benchmark OpenClaw models for performance comparison. Results should be run fresh — don't rely on stale cached data.

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

## Running a Benchmark

1. Create project directory: `mkdir -p ~/openclaw/projects/model-benchmark-$(date +%Y-%m-%d)`
2. Spawn isolated sessions for each model with the task template above
3. Collect metrics and write `benchmark_report.md` comparing results
4. Previous benchmark outputs (if they exist) are in `~/openclaw/projects/model-benchmark-*/`
