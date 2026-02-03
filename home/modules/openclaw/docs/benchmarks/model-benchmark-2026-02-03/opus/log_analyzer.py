#!/usr/bin/env python3
"""
Systemd Journal Log Analyzer

Parses systemd journal logs, extracts error patterns grouped by service,
and generates JSON/markdown reports with optional webhook posting.
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime
from typing import Any


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze systemd journal logs and extract error patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --since "1 hour ago" --output report
  %(prog)s --priority err --webhook https://example.com/hook
  %(prog)s --services nginx postgresql --dry-run
        """,
    )
    parser.add_argument(
        "--since",
        default="24 hours ago",
        help="Start time for log analysis (default: '24 hours ago')",
    )
    parser.add_argument(
        "--until",
        default=None,
        help="End time for log analysis (default: now)",
    )
    parser.add_argument(
        "--priority",
        choices=["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"],
        default="err",
        help="Minimum priority level to include (default: err)",
    )
    parser.add_argument(
        "--services",
        nargs="+",
        default=None,
        help="Filter to specific service names (default: all services)",
    )
    parser.add_argument(
        "--output",
        default="log_analysis",
        help="Base filename for output reports (default: log_analysis)",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for output files (default: current directory)",
    )
    parser.add_argument(
        "--webhook",
        default=None,
        help="Webhook URL to POST results to",
    )
    parser.add_argument(
        "--webhook-timeout",
        type=int,
        default=30,
        help="Webhook request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Generate only JSON output (skip markdown)",
    )
    parser.add_argument(
        "--markdown-only",
        action="store_true",
        help="Generate only markdown output (skip JSON)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-error output",
    )
    return parser.parse_args()


def log(message: str, args: argparse.Namespace, is_error: bool = False) -> None:
    """Print message respecting verbosity settings."""
    if is_error:
        print(f"ERROR: {message}", file=sys.stderr)
    elif not args.quiet:
        print(message)


def verbose_log(message: str, args: argparse.Namespace) -> None:
    """Print message only if verbose mode is enabled."""
    if args.verbose and not args.quiet:
        print(f"  [verbose] {message}")


def fetch_journal_logs(args: argparse.Namespace) -> list[dict[str, Any]]:
    """
    Fetch logs from systemd journal using journalctl.
    
    Returns a list of log entries as dictionaries.
    """
    cmd = [
        "journalctl",
        "--output=json",
        f"--since={args.since}",
        f"--priority={args.priority}",
        "--no-pager",
    ]
    
    if args.until:
        cmd.append(f"--until={args.until}")
    
    if args.services:
        for service in args.services:
            # Handle both "service" and "service.service" formats
            unit = service if service.endswith(".service") else f"{service}.service"
            cmd.extend(["--unit", unit])
    
    verbose_log(f"Running: {' '.join(cmd)}", args)
    
    if args.dry_run:
        log("[DRY-RUN] Would execute journalctl command", args)
        return []
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        
        if result.returncode != 0:
            # journalctl returns 1 if no entries found, which is OK
            if "No entries" in result.stderr or not result.stderr.strip():
                verbose_log("No journal entries found matching criteria", args)
                return []
            raise RuntimeError(f"journalctl failed: {result.stderr}")
        
        entries = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as e:
                    verbose_log(f"Skipping malformed JSON line: {e}", args)
                    continue
        
        verbose_log(f"Fetched {len(entries)} log entries", args)
        return entries
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("journalctl command timed out after 120 seconds")
    except FileNotFoundError:
        raise RuntimeError("journalctl not found - is systemd installed?")
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Failed to run journalctl: {e}")


def extract_error_patterns(
    entries: list[dict[str, Any]], args: argparse.Namespace
) -> dict[str, Any]:
    """
    Extract and group error patterns by service name.
    
    Returns a structured dictionary with analysis results.
    """
    services: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "count": 0,
            "patterns": defaultdict(lambda: {"count": 0, "examples": []}),
            "first_seen": None,
            "last_seen": None,
        }
    )
    
    # Common error patterns to extract
    error_patterns = [
        (r"(?i)failed to (\w+)", "failed_to"),
        (r"(?i)error[:\s]+(.{0,50})", "error_message"),
        (r"(?i)cannot (\w+)", "cannot"),
        (r"(?i)unable to (\w+)", "unable_to"),
        (r"(?i)permission denied", "permission_denied"),
        (r"(?i)connection (?:refused|reset|timed out)", "connection_issue"),
        (r"(?i)out of memory", "oom"),
        (r"(?i)segmentation fault|segfault", "segfault"),
        (r"(?i)timeout", "timeout"),
        (r"(?i)fatal[:\s]+(.{0,50})", "fatal"),
    ]
    
    for entry in entries:
        # Extract service name from various fields
        service = (
            entry.get("_SYSTEMD_UNIT")
            or entry.get("SYSLOG_IDENTIFIER")
            or entry.get("_COMM")
            or "unknown"
        )
        
        # Clean up service name
        service = service.replace(".service", "")
        
        message = entry.get("MESSAGE", "")
        if isinstance(message, list):
            message = " ".join(str(m) for m in message)
        message = str(message)
        
        # Get timestamp
        timestamp_usec = entry.get("__REALTIME_TIMESTAMP")
        if timestamp_usec:
            try:
                timestamp = datetime.fromtimestamp(int(timestamp_usec) / 1_000_000)
                timestamp_str = timestamp.isoformat()
            except (ValueError, OSError):
                timestamp_str = None
        else:
            timestamp_str = None
        
        # Update service stats
        svc = services[service]
        svc["count"] += 1
        
        if timestamp_str:
            if svc["first_seen"] is None or timestamp_str < svc["first_seen"]:
                svc["first_seen"] = timestamp_str
            if svc["last_seen"] is None or timestamp_str > svc["last_seen"]:
                svc["last_seen"] = timestamp_str
        
        # Match error patterns
        matched = False
        for pattern, pattern_name in error_patterns:
            match = re.search(pattern, message)
            if match:
                matched = True
                pattern_data = svc["patterns"][pattern_name]
                pattern_data["count"] += 1
                
                # Keep up to 3 example messages
                if len(pattern_data["examples"]) < 3:
                    pattern_data["examples"].append({
                        "message": message[:200],  # Truncate long messages
                        "timestamp": timestamp_str,
                    })
        
        # If no pattern matched, categorize as "other"
        if not matched:
            pattern_data = svc["patterns"]["other"]
            pattern_data["count"] += 1
            if len(pattern_data["examples"]) < 3:
                pattern_data["examples"].append({
                    "message": message[:200],
                    "timestamp": timestamp_str,
                })
    
    # Convert defaultdicts to regular dicts for JSON serialization
    result = {
        "analysis_time": datetime.now().isoformat(),
        "parameters": {
            "since": args.since,
            "until": args.until,
            "priority": args.priority,
            "services_filter": args.services,
        },
        "summary": {
            "total_entries": len(entries),
            "services_affected": len(services),
        },
        "services": {},
    }
    
    for service_name, svc_data in sorted(services.items(), key=lambda x: -x[1]["count"]):
        result["services"][service_name] = {
            "count": svc_data["count"],
            "first_seen": svc_data["first_seen"],
            "last_seen": svc_data["last_seen"],
            "patterns": {
                name: dict(data) for name, data in svc_data["patterns"].items()
            },
        }
    
    verbose_log(
        f"Analyzed {len(entries)} entries across {len(services)} services", args
    )
    return result


def generate_markdown_report(analysis: dict[str, Any]) -> str:
    """Generate a markdown-formatted report from analysis results."""
    lines = [
        "# Systemd Journal Log Analysis Report",
        "",
        f"**Generated:** {analysis['analysis_time']}",
        "",
        "## Parameters",
        "",
        f"- **Since:** {analysis['parameters']['since']}",
        f"- **Until:** {analysis['parameters']['until'] or 'now'}",
        f"- **Priority:** {analysis['parameters']['priority']}",
        f"- **Services Filter:** {analysis['parameters']['services_filter'] or 'all'}",
        "",
        "## Summary",
        "",
        f"- **Total Entries:** {analysis['summary']['total_entries']}",
        f"- **Services Affected:** {analysis['summary']['services_affected']}",
        "",
    ]
    
    if not analysis["services"]:
        lines.append("*No errors found matching the specified criteria.*")
        return "\n".join(lines)
    
    lines.extend([
        "## Errors by Service",
        "",
    ])
    
    for service_name, svc_data in analysis["services"].items():
        lines.extend([
            f"### {service_name}",
            "",
            f"**Total Errors:** {svc_data['count']}",
            "",
        ])
        
        if svc_data["first_seen"]:
            lines.append(f"**Time Range:** {svc_data['first_seen']} → {svc_data['last_seen']}")
            lines.append("")
        
        lines.append("#### Error Patterns")
        lines.append("")
        lines.append("| Pattern | Count |")
        lines.append("|---------|-------|")
        
        for pattern_name, pattern_data in sorted(
            svc_data["patterns"].items(), key=lambda x: -x[1]["count"]
        ):
            lines.append(f"| {pattern_name} | {pattern_data['count']} |")
        
        lines.append("")
        
        # Show example messages
        lines.append("#### Example Messages")
        lines.append("")
        
        examples_shown = 0
        for pattern_name, pattern_data in svc_data["patterns"].items():
            for example in pattern_data["examples"][:2]:
                if examples_shown >= 5:
                    break
                msg = example["message"].replace("|", "\\|").replace("\n", " ")
                ts = example["timestamp"] or "unknown time"
                lines.append(f"- `[{ts}]` {msg}")
                examples_shown += 1
            if examples_shown >= 5:
                break
        
        lines.append("")
    
    return "\n".join(lines)


def write_reports(
    analysis: dict[str, Any], args: argparse.Namespace
) -> tuple[str | None, str | None]:
    """
    Write JSON and/or markdown reports to files.
    
    Returns tuple of (json_path, markdown_path) for files written.
    """
    import os
    
    json_path = None
    md_path = None
    
    output_dir = args.output_dir
    base_name = args.output
    
    # Ensure output directory exists
    if not args.dry_run:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create output directory: {e}")
    
    # Write JSON report
    if not args.markdown_only:
        json_path = os.path.join(output_dir, f"{base_name}.json")
        
        if args.dry_run:
            log(f"[DRY-RUN] Would write JSON report to: {json_path}", args)
        else:
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(analysis, f, indent=2, ensure_ascii=False)
                verbose_log(f"Wrote JSON report: {json_path}", args)
            except IOError as e:
                raise RuntimeError(f"Failed to write JSON report: {e}")
    
    # Write markdown report
    if not args.json_only:
        md_path = os.path.join(output_dir, f"{base_name}.md")
        markdown = generate_markdown_report(analysis)
        
        if args.dry_run:
            log(f"[DRY-RUN] Would write markdown report to: {md_path}", args)
        else:
            try:
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(markdown)
                verbose_log(f"Wrote markdown report: {md_path}", args)
            except IOError as e:
                raise RuntimeError(f"Failed to write markdown report: {e}")
    
    return json_path, md_path


def post_to_webhook(
    analysis: dict[str, Any], webhook_url: str, args: argparse.Namespace
) -> bool:
    """
    POST analysis results to a webhook URL.
    
    Returns True on success, False on failure.
    """
    if args.dry_run:
        log(f"[DRY-RUN] Would POST results to webhook: {webhook_url}", args)
        return True
    
    try:
        payload = json.dumps(analysis, ensure_ascii=False).encode("utf-8")
        
        request = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "log-analyzer/1.0",
            },
            method="POST",
        )
        
        verbose_log(f"POSTing {len(payload)} bytes to {webhook_url}", args)
        
        with urllib.request.urlopen(request, timeout=args.webhook_timeout) as response:
            status = response.status
            verbose_log(f"Webhook response status: {status}", args)
            return 200 <= status < 300
            
    except urllib.error.HTTPError as e:
        log(f"Webhook HTTP error: {e.code} {e.reason}", args, is_error=True)
        return False
    except urllib.error.URLError as e:
        log(f"Webhook URL error: {e.reason}", args, is_error=True)
        return False
    except ValueError as e:
        log(f"Invalid webhook URL: {e}", args, is_error=True)
        return False
    except TimeoutError:
        log(f"Webhook request timed out after {args.webhook_timeout}s", args, is_error=True)
        return False


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Validate conflicting options
    if args.json_only and args.markdown_only:
        log("Cannot specify both --json-only and --markdown-only", args, is_error=True)
        return 1
    
    if args.verbose and args.quiet:
        log("Cannot specify both --verbose and --quiet", args, is_error=True)
        return 1
    
    try:
        # Step 1: Fetch journal logs
        log(f"Fetching journal logs since '{args.since}'...", args)
        entries = fetch_journal_logs(args)
        
        if not entries and not args.dry_run:
            log("No log entries found matching criteria", args)
        
        # Step 2: Extract and analyze error patterns
        log("Analyzing error patterns...", args)
        analysis = extract_error_patterns(entries, args)
        
        # Step 3: Write reports
        log("Generating reports...", args)
        json_path, md_path = write_reports(analysis, args)
        
        if json_path and not args.dry_run:
            log(f"JSON report: {json_path}", args)
        if md_path and not args.dry_run:
            log(f"Markdown report: {md_path}", args)
        
        # Step 4: POST to webhook if configured
        if args.webhook:
            log(f"Posting to webhook...", args)
            success = post_to_webhook(analysis, args.webhook, args)
            if not success:
                log("Webhook POST failed", args, is_error=True)
                return 1
            log("Webhook POST successful", args)
        
        # Summary
        summary = analysis["summary"]
        log(
            f"Analysis complete: {summary['total_entries']} errors across "
            f"{summary['services_affected']} services",
            args,
        )
        
        return 0
        
    except RuntimeError as e:
        log(str(e), args, is_error=True)
        return 1
    except KeyboardInterrupt:
        log("Interrupted", args, is_error=True)
        return 130


if __name__ == "__main__":
    sys.exit(main())
