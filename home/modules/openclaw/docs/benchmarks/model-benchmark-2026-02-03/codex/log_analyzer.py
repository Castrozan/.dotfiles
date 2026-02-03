#!/usr/bin/env python3
"""Systemd journal error analyzer.

Parses journalctl output, groups error patterns by service, generates JSON
and Markdown reports, and optionally posts results to a webhook.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple
from urllib import request


@dataclass
class LogEntry:
    service: str
    message: str


@dataclass
class Report:
    generated_at: str
    since: str
    until: str
    total_errors: int
    services: Dict[str, Dict[str, int]]


ERROR_LEVELS = {"err", "error", "crit", "alert", "emerg"}


def run_journalctl(since: str, until: str, units: Optional[List[str]],
                   priority: Optional[str], timeout: int) -> str:
    cmd = ["journalctl", "--no-pager", "-o", "short-iso"]
    if since:
        cmd += ["--since", since]
    if until:
        cmd += ["--until", until]
    if priority:
        cmd += ["-p", priority]
    if units:
        for unit in units:
            cmd += ["-u", unit]
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Failed to run journalctl: {exc}") from exc

    if completed.returncode != 0:
        raise RuntimeError(
            f"journalctl failed ({completed.returncode}): {completed.stderr.strip()}"
        )
    return completed.stdout


def parse_entries(text: str) -> List[LogEntry]:
    entries: List[LogEntry] = []
    # Example line: 2026-02-03T12:34:56-0300 host systemd[1]: Started ...
    line_re = re.compile(r"^\S+\s+\S+\s+(?P<svc>[^\s:]+)(?:\[[0-9]+\])?:\s+(?P<msg>.*)$")
    for line in text.splitlines():
        match = line_re.match(line)
        if not match:
            continue
        svc = match.group("svc")
        msg = match.group("msg").strip()
        if not msg:
            continue
        entries.append(LogEntry(service=svc, message=msg))
    return entries


def normalize_message(message: str) -> str:
    # Normalize numbers/hex/uuids to reduce noise
    msg = re.sub(r"0x[0-9a-fA-F]+", "<HEX>", message)
    msg = re.sub(r"\b[0-9a-fA-F]{8}\b(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b", "<UUID>", msg)
    msg = re.sub(r"\b\d+\b", "<NUM>", msg)
    msg = re.sub(r"\s+", " ", msg).strip()
    return msg


def filter_errors(entries: Iterable[LogEntry]) -> List[LogEntry]:
    errors: List[LogEntry] = []
    err_re = re.compile(r"\b(error|failed|failure|panic|fatal|segfault|oom)\b", re.IGNORECASE)
    for entry in entries:
        if err_re.search(entry.message):
            errors.append(entry)
    return errors


def group_errors(entries: Iterable[LogEntry]) -> Dict[str, Counter]:
    grouped: Dict[str, Counter] = defaultdict(Counter)
    for entry in entries:
        pattern = normalize_message(entry.message)
        grouped[entry.service][pattern] += 1
    return grouped


def build_report(grouped: Dict[str, Counter], since: str, until: str) -> Report:
    services: Dict[str, Dict[str, int]] = {}
    total = 0
    for svc, counter in grouped.items():
        services[svc] = dict(counter.most_common())
        total += sum(counter.values())
    return Report(
        generated_at=datetime.now(timezone.utc).isoformat(),
        since=since,
        until=until,
        total_errors=total,
        services=services,
    )


def write_json(report: Report, path: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, sort_keys=True)
    except OSError as exc:
        raise RuntimeError(f"Failed to write JSON report: {exc}") from exc


def write_markdown(report: Report, path: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Journal Error Summary\n\n")
            f.write(f"Generated at: {report.generated_at}\n\n")
            f.write(f"Range: {report.since or 'beginning'} → {report.until or 'now'}\n\n")
            f.write(f"Total errors: **{report.total_errors}**\n\n")
            for svc, patterns in report.services.items():
                f.write(f"## {svc}\n\n")
                for pattern, count in patterns.items():
                    f.write(f"- {count} × `{pattern}`\n")
                f.write("\n")
    except OSError as exc:
        raise RuntimeError(f"Failed to write Markdown report: {exc}") from exc


def post_webhook(url: str, report: Report, timeout: int, dry_run: bool) -> None:
    if dry_run:
        return
    payload = json.dumps(asdict(report)).encode("utf-8")
    req = request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            if resp.status < 200 or resp.status >= 300:
                raise RuntimeError(f"Webhook returned status {resp.status}")
    except Exception as exc:  # noqa: BLE001 - wrap all request issues
        raise RuntimeError(f"Failed to POST webhook: {exc}") from exc


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze systemd journal errors")
    parser.add_argument("--since", default="", help="Start time for journalctl")
    parser.add_argument("--until", default="", help="End time for journalctl")
    parser.add_argument("--unit", action="append", dest="units", help="Filter by systemd unit (repeatable)")
    parser.add_argument("--priority", default="err", help="journalctl priority (default: err)")
    parser.add_argument("--json-out", required=True, help="Path to JSON report")
    parser.add_argument("--md-out", required=True, help="Path to Markdown report")
    parser.add_argument("--webhook", default="", help="Webhook URL for POSTing results")
    parser.add_argument("--timeout", type=int, default=15, help="Timeout in seconds for commands and webhook")
    parser.add_argument("--dry-run", action="store_true", help="Run without posting webhook")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    start = time.time()
    try:
        text = run_journalctl(args.since, args.until, args.units, args.priority, args.timeout)
        entries = parse_entries(text)
        errors = filter_errors(entries)
        grouped = group_errors(errors)
        report = build_report(grouped, args.since, args.until)
        write_json(report, args.json_out)
        write_markdown(report, args.md_out)
        if args.webhook:
            post_webhook(args.webhook, report, args.timeout, args.dry_run)
    except Exception as exc:  # noqa: BLE001 - top-level guard
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    finally:
        _ = time.time() - start
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
