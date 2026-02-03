#!/usr/bin/env python3
"""Systemd journal log analyzer.

- Uses journalctl to fetch logs in JSON format
- Extracts error patterns grouped by service name
- Generates JSON and Markdown summary reports
- Optionally posts results to a webhook URL
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Tuple

ERROR_REGEX = re.compile(
    r"\b(error|failed|failure|panic|fatal|exception|traceback|segfault|segmentation fault)\b",
    re.IGNORECASE,
)


def run_journalctl(args: argparse.Namespace) -> Iterable[dict]:
    """Run journalctl and yield parsed JSON entries."""
    cmd = [
        "journalctl",
        "-o",
        "json",
        "--no-pager",
    ]
    if args.unit:
        cmd += ["-u", args.unit]
    if args.since:
        cmd += ["--since", args.since]
    if args.until:
        cmd += ["--until", args.until]
    if args.boot:
        cmd += ["-b", args.boot]
    if args.priority:
        cmd += ["-p", args.priority]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("journalctl not found on PATH") from exc

    assert proc.stdout is not None
    assert proc.stderr is not None

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            # Skip malformed entries
            continue

    stderr = proc.stderr.read()
    return_code = proc.wait()
    if return_code != 0:
        raise RuntimeError(f"journalctl failed: {stderr.strip()}")


def normalize_message(msg: str) -> str:
    """Normalize message to reduce cardinality for grouping."""
    msg = re.sub(r"\s+", " ", msg.strip())
    msg = re.sub(r"0x[0-9a-fA-F]+", "<hex>", msg)
    msg = re.sub(r"\b\d+\b", "<num>", msg)
    return msg


def entry_service(entry: dict) -> str:
    """Best-effort service name for an entry."""
    return (
        entry.get("_SYSTEMD_UNIT")
        or entry.get("SYSLOG_IDENTIFIER")
        or entry.get("_COMM")
        or "unknown"
    )


def is_error_entry(entry: dict) -> bool:
    msg = entry.get("MESSAGE", "")
    if not isinstance(msg, str):
        return False
    # If user set priority filter, journalctl already filtered; still check regex
    return bool(ERROR_REGEX.search(msg))


def analyze(entries: Iterable[dict]) -> Dict[str, Dict[str, int]]:
    """Return mapping service -> pattern -> count."""
    grouped: Dict[str, Counter] = defaultdict(Counter)
    for entry in entries:
        if not is_error_entry(entry):
            continue
        service = entry_service(entry)
        msg = entry.get("MESSAGE", "")
        pattern = normalize_message(msg)
        grouped[service][pattern] += 1

    return {svc: dict(cnt) for svc, cnt in grouped.items()}


def build_report(data: Dict[str, Dict[str, int]], args: argparse.Namespace) -> dict:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    return {
        "generated_at": now,
        "filters": {
            "unit": args.unit,
            "since": args.since,
            "until": args.until,
            "boot": args.boot,
            "priority": args.priority,
        },
        "services": data,
    }


def write_json_report(report: dict, path: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise RuntimeError(f"Failed to write JSON report: {exc}") from exc


def write_markdown_report(report: dict, path: str) -> None:
    try:
        lines: List[str] = []
        lines.append("# Journal Error Summary")
        lines.append("")
        lines.append(f"Generated at: `{report['generated_at']}`")
        lines.append("")
        lines.append("## Filters")
        lines.append("" )
        for k, v in report["filters"].items():
            lines.append(f"- **{k}**: `{v}`")
        lines.append("")
        lines.append("## Services")
        lines.append("")
        services: Dict[str, Dict[str, int]] = report.get("services", {})
        if not services:
            lines.append("_No error entries found._")
        else:
            for svc, patterns in sorted(services.items()):
                lines.append(f"### {svc}")
                lines.append("")
                for pattern, count in sorted(
                    patterns.items(), key=lambda x: (-x[1], x[0])
                ):
                    lines.append(f"- **{count}x** {pattern}")
                lines.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError as exc:
        raise RuntimeError(f"Failed to write Markdown report: {exc}") from exc


def post_webhook(report: dict, url: str, timeout: int = 10) -> Tuple[int, str]:
    data = json.dumps(report).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Webhook HTTP error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Webhook request failed: {exc}") from exc


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze systemd journal errors")
    p.add_argument("--unit", help="Systemd unit name (journalctl -u)")
    p.add_argument("--since", help="Start time (journalctl --since)")
    p.add_argument("--until", help="End time (journalctl --until)")
    p.add_argument("--boot", help="Boot ID or offset (journalctl -b)")
    p.add_argument(
        "--priority",
        help="Systemd priority filter (journalctl -p), e.g. err, warning",
    )
    p.add_argument(
        "--json-out",
        default="journal_errors.json",
        help="Path to JSON report",
    )
    p.add_argument(
        "--md-out",
        default="journal_errors.md",
        help="Path to Markdown report",
    )
    p.add_argument("--webhook-url", help="Webhook URL to POST results")
    p.add_argument(
        "--webhook-timeout",
        type=int,
        default=10,
        help="Webhook request timeout in seconds",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Run analysis without posting webhook",
    )
    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    try:
        entries = run_journalctl(args)
        data = analyze(entries)
        report = build_report(data, args)
        write_json_report(report, args.json_out)
        write_markdown_report(report, args.md_out)
        if args.webhook_url:
            if args.dry_run:
                print("[dry-run] Skipping webhook POST")
            else:
                status, _ = post_webhook(report, args.webhook_url, args.webhook_timeout)
                print(f"Webhook POST status: {status}")
        return 0
    except Exception as exc:  # pragma: no cover - top-level safety
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
