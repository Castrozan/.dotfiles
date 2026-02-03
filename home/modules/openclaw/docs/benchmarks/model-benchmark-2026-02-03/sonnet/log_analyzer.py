#!/usr/bin/env python3
"""
Systemd Journal Log Analyzer

Parses systemd journal logs, extracts error patterns grouped by service,
generates JSON and markdown reports, and optionally POSTs to a webhook.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib import request
from urllib.error import URLError, HTTPError


class LogAnalyzer:
    """Analyzes systemd journal logs for error patterns."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.error_patterns = [
            r'error',
            r'fail(?:ed|ure)?',
            r'critical',
            r'fatal',
            r'panic',
            r'exception',
            r'segfault',
            r'core dump',
        ]
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.error_patterns
        ]

    def fetch_journal_logs(
        self, 
        since: Optional[str] = None,
        until: Optional[str] = None,
        unit: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> str:
        """
        Fetch logs from systemd journal using journalctl.

        Args:
            since: Start time for log retrieval (journalctl format)
            until: End time for log retrieval (journalctl format)
            unit: Specific systemd unit to query
            priority: Log priority level (0-7 or emerg-debug)

        Returns:
            Raw journal output as string

        Raises:
            subprocess.CalledProcessError: If journalctl fails
        """
        cmd = ['journalctl', '--no-pager', '--output=json']

        if since:
            cmd.extend(['--since', since])
        if until:
            cmd.extend(['--until', until])
        if unit:
            cmd.extend(['--unit', unit])
        if priority:
            cmd.extend(['--priority', priority])

        try:
            if self.dry_run:
                print(f"[DRY-RUN] Would execute: {' '.join(cmd)}")
                return '{"MESSAGE":"dry-run-log","_SYSTEMD_UNIT":"test.service"}\n'

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,
            )
            return result.stdout

        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"journalctl command timed out after 300s") from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"journalctl failed with exit code {e.returncode}: {e.stderr}"
            ) from e
        except FileNotFoundError as e:
            raise RuntimeError(
                "journalctl not found. Is systemd installed?"
            ) from e

    def parse_logs(self, raw_logs: str) -> List[Dict]:
        """
        Parse raw JSON-formatted journal logs.

        Args:
            raw_logs: Raw output from journalctl --output=json

        Returns:
            List of parsed log entries as dictionaries
        """
        entries = []
        for line in raw_logs.strip().split('\n'):
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse log line: {e}", file=sys.stderr)
                continue
        return entries

    def extract_errors(self, entries: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract error entries grouped by service name.

        Args:
            entries: Parsed log entries

        Returns:
            Dictionary mapping service names to error entries
        """
        errors_by_service = defaultdict(list)

        for entry in entries:
            message = entry.get('MESSAGE', '')
            if not message:
                continue

            # Check if message matches any error pattern
            if any(pattern.search(message) for pattern in self.compiled_patterns):
                service = entry.get('_SYSTEMD_UNIT', 'unknown')
                
                error_entry = {
                    'timestamp': entry.get('__REALTIME_TIMESTAMP', ''),
                    'message': message,
                    'priority': entry.get('PRIORITY', ''),
                    'pid': entry.get('_PID', ''),
                }
                
                errors_by_service[service].append(error_entry)

        return dict(errors_by_service)

    def generate_json_report(
        self, 
        errors: Dict[str, List[Dict]],
        output_file: Optional[Path] = None,
    ) -> str:
        """
        Generate JSON report of errors.

        Args:
            errors: Errors grouped by service
            output_file: Optional file path to write report

        Returns:
            JSON string of the report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_services_with_errors': len(errors),
            'total_error_entries': sum(len(v) for v in errors.values()),
            'errors_by_service': errors,
        }

        json_str = json.dumps(report, indent=2)

        if output_file:
            try:
                if self.dry_run:
                    print(f"[DRY-RUN] Would write JSON to: {output_file}")
                else:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(json_str)
                    print(f"JSON report written to: {output_file}")
            except IOError as e:
                print(f"Error writing JSON report: {e}", file=sys.stderr)

        return json_str

    def generate_markdown_report(
        self,
        errors: Dict[str, List[Dict]],
        output_file: Optional[Path] = None,
    ) -> str:
        """
        Generate markdown report of errors.

        Args:
            errors: Errors grouped by service
            output_file: Optional file path to write report

        Returns:
            Markdown string of the report
        """
        lines = [
            "# Systemd Journal Error Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**Total Services with Errors:** {len(errors)}",
            f"**Total Error Entries:** {sum(len(v) for v in errors.values())}",
            "",
            "---",
            "",
        ]

        for service, service_errors in sorted(errors.items()):
            lines.append(f"## {service}")
            lines.append("")
            lines.append(f"**Error Count:** {len(service_errors)}")
            lines.append("")

            # Show up to 10 most recent errors per service
            display_errors = service_errors[-10:]
            
            for error in display_errors:
                timestamp = error.get('timestamp', 'N/A')
                if timestamp != 'N/A' and timestamp:
                    try:
                        # Convert microseconds since epoch to datetime
                        ts_sec = int(timestamp) / 1000000
                        dt = datetime.fromtimestamp(ts_sec)
                        timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        pass

                message = error.get('message', 'N/A')
                priority = error.get('priority', 'N/A')
                
                lines.append(f"- **{timestamp}** [Priority: {priority}]")
                lines.append(f"  ```")
                lines.append(f"  {message}")
                lines.append(f"  ```")
                lines.append("")

            if len(service_errors) > 10:
                lines.append(f"*({len(service_errors) - 10} more errors not shown)*")
                lines.append("")

            lines.append("---")
            lines.append("")

        md_str = '\n'.join(lines)

        if output_file:
            try:
                if self.dry_run:
                    print(f"[DRY-RUN] Would write markdown to: {output_file}")
                else:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(md_str)
                    print(f"Markdown report written to: {output_file}")
            except IOError as e:
                print(f"Error writing markdown report: {e}", file=sys.stderr)

        return md_str

    def post_to_webhook(self, webhook_url: str, data: str) -> bool:
        """
        POST report data to webhook URL.

        Args:
            webhook_url: Target webhook URL
            data: JSON data to send

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print(f"[DRY-RUN] Would POST to: {webhook_url}")
            print(f"[DRY-RUN] Payload size: {len(data)} bytes")
            return True

        try:
            req = request.Request(
                webhook_url,
                data=data.encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'SystemdLogAnalyzer/1.0',
                },
                method='POST',
            )

            with request.urlopen(req, timeout=30) as response:
                status_code = response.getcode()
                if 200 <= status_code < 300:
                    print(f"Successfully posted to webhook (status: {status_code})")
                    return True
                else:
                    print(
                        f"Webhook returned non-2xx status: {status_code}",
                        file=sys.stderr,
                    )
                    return False

        except HTTPError as e:
            print(
                f"HTTP error posting to webhook: {e.code} - {e.reason}",
                file=sys.stderr,
            )
            return False
        except URLError as e:
            print(f"URL error posting to webhook: {e.reason}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Unexpected error posting to webhook: {e}", file=sys.stderr)
            return False


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze systemd journal logs for error patterns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --since "1 hour ago" --json-output errors.json
  %(prog)s --unit nginx.service --webhook https://example.com/hook
  %(prog)s --priority err --dry-run
  %(prog)s --since "2026-02-03 00:00:00" --until "2026-02-03 23:59:59"
        """,
    )

    parser.add_argument(
        '--since',
        metavar='TIME',
        help='Start time for log retrieval (e.g., "1 hour ago", "2026-02-03")',
    )
    parser.add_argument(
        '--until',
        metavar='TIME',
        help='End time for log retrieval (e.g., "now", "2026-02-03 23:59:59")',
    )
    parser.add_argument(
        '--unit',
        metavar='UNIT',
        help='Specific systemd unit to analyze (e.g., nginx.service)',
    )
    parser.add_argument(
        '--priority',
        metavar='PRIORITY',
        help='Log priority level (0-7 or emerg/alert/crit/err/warning/notice/info/debug)',
    )
    parser.add_argument(
        '--json-output',
        metavar='FILE',
        type=Path,
        help='Write JSON report to specified file',
    )
    parser.add_argument(
        '--markdown-output',
        metavar='FILE',
        type=Path,
        help='Write markdown report to specified file',
    )
    parser.add_argument(
        '--webhook',
        metavar='URL',
        help='POST JSON report to webhook URL',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it',
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output',
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_arguments()

    try:
        # Initialize analyzer
        analyzer = LogAnalyzer(dry_run=args.dry_run)

        if args.verbose:
            print("Fetching journal logs...")

        # Fetch logs
        raw_logs = analyzer.fetch_journal_logs(
            since=args.since,
            until=args.until,
            unit=args.unit,
            priority=args.priority,
        )

        if args.verbose:
            print(f"Fetched {len(raw_logs.splitlines())} log lines")
            print("Parsing logs...")

        # Parse logs
        entries = analyzer.parse_logs(raw_logs)

        if args.verbose:
            print(f"Parsed {len(entries)} log entries")
            print("Extracting errors...")

        # Extract errors
        errors = analyzer.extract_errors(entries)

        if args.verbose:
            print(f"Found errors in {len(errors)} services")

        # Generate reports
        json_report = analyzer.generate_json_report(
            errors,
            output_file=args.json_output,
        )

        if args.markdown_output:
            analyzer.generate_markdown_report(
                errors,
                output_file=args.markdown_output,
            )

        # Post to webhook if specified
        if args.webhook:
            success = analyzer.post_to_webhook(args.webhook, json_report)
            if not success:
                print("Warning: Failed to post to webhook", file=sys.stderr)
                return 1

        # Print summary to stdout if no output files specified
        if not args.json_output and not args.markdown_output and not args.webhook:
            print("\n" + "="*60)
            print("ERROR SUMMARY")
            print("="*60)
            for service, service_errors in sorted(errors.items()):
                print(f"\n{service}: {len(service_errors)} errors")
            print("\nUse --json-output or --markdown-output to save reports")

        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
