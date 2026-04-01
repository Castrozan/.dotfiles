import argparse
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

DATABASE_DIRECTORY = Path(
    os.environ.get(
        "SOPHOS_MONITOR_DATA_DIR",
        os.path.expanduser("~/.local/share/sophos-monitor"),
    )
)
DATABASE_PATH = DATABASE_DIRECTORY / "metrics.db"


def format_bytes_as_megabytes(byte_count: int) -> str:
    return f"{byte_count / (1024 * 1024):.0f}MB"


def format_epoch_as_local_datetime(epoch: float) -> str:
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")


def show_latest_snapshot(connection: sqlite3.Connection) -> None:
    snapshot = connection.execute(
        "SELECT id, timestamp_epoch, total_resident_set_size_bytes, "
        "total_cpu_percent, process_count FROM snapshots "
        "ORDER BY timestamp_epoch DESC LIMIT 1"
    ).fetchone()

    if not snapshot:
        print("No snapshots found.")
        return

    snapshot_id, timestamp, total_rss, total_cpu, process_count = snapshot
    print(f"Latest snapshot: {format_epoch_as_local_datetime(timestamp)}")
    print(
        f"  Total: {process_count} processes, "
        f"{format_bytes_as_megabytes(total_rss)} RSS, "
        f"{total_cpu:.1f}% CPU"
    )
    print()

    processes = connection.execute(
        "SELECT name, pid, cpu_percent, memory_percent, "
        "resident_set_size_bytes, thread_count, cpu_time_seconds, state "
        "FROM process_metrics WHERE snapshot_id = ? "
        "ORDER BY resident_set_size_bytes DESC",
        (snapshot_id,),
    ).fetchall()

    header = (
        f"{'Name':<25} {'PID':>7} {'CPU%':>6} {'MEM%':>6}"
        f" {'RSS':>8} {'Thr':>4} {'CPUTime':>10} {'St':>3}"
    )
    print(header)
    print("-" * 75)
    for name, pid, cpu, mem, rss, threads, cpu_time, state in processes:
        hours = int(cpu_time // 3600)
        minutes = int((cpu_time % 3600) // 60)
        print(
            f"{name:<25} {pid:>7} {cpu:>5.1f}% {mem:>5.1f}% "
            f"{format_bytes_as_megabytes(rss):>8} {threads:>4} "
            f"{hours:>4}h{minutes:02d}m {state:>3}"
        )


def show_timeline_summary(connection: sqlite3.Connection, hours: int) -> None:
    cutoff_epoch = time.time() - (hours * 3600)
    snapshots = connection.execute(
        "SELECT timestamp_epoch, total_resident_set_size_bytes, "
        "total_cpu_percent, process_count FROM snapshots "
        "WHERE timestamp_epoch >= ? ORDER BY timestamp_epoch",
        (cutoff_epoch,),
    ).fetchall()

    if not snapshots:
        print(f"No snapshots in the last {hours} hours.")
        return

    print(f"Timeline: last {hours} hours ({len(snapshots)} snapshots)")
    print()
    print(f"{'Timestamp':<20} {'Procs':>6} {'RSS':>10} {'CPU%':>7}")
    print("-" * 47)
    for timestamp, total_rss, total_cpu, process_count in snapshots:
        print(
            f"{format_epoch_as_local_datetime(timestamp):<20} "
            f"{process_count:>6} "
            f"{format_bytes_as_megabytes(total_rss):>10} "
            f"{total_cpu:>6.1f}%"
        )

    rss_values = [s[1] for s in snapshots]
    cpu_values = [s[2] for s in snapshots]
    print()
    print(
        f"RSS  — min: {format_bytes_as_megabytes(min(rss_values))}, "
        f"max: {format_bytes_as_megabytes(max(rss_values))}, "
        f"avg: {format_bytes_as_megabytes(sum(rss_values) // len(rss_values))}"
    )
    print(
        f"CPU% — min: {min(cpu_values):.1f}%, "
        f"max: {max(cpu_values):.1f}%, "
        f"avg: {sum(cpu_values) / len(cpu_values):.1f}%"
    )


def show_top_consumers(connection: sqlite3.Connection, hours: int) -> None:
    cutoff_epoch = time.time() - (hours * 3600)
    processes = connection.execute(
        "SELECT pm.name, "
        "AVG(pm.cpu_percent) as avg_cpu, "
        "MAX(pm.cpu_percent) as max_cpu, "
        "AVG(pm.resident_set_size_bytes) as avg_rss, "
        "MAX(pm.resident_set_size_bytes) as max_rss, "
        "COUNT(DISTINCT pm.snapshot_id) as appearances "
        "FROM process_metrics pm "
        "JOIN snapshots s ON pm.snapshot_id = s.id "
        "WHERE s.timestamp_epoch >= ? "
        "GROUP BY pm.name "
        "ORDER BY avg_rss DESC",
        (cutoff_epoch,),
    ).fetchall()

    if not processes:
        print(f"No data in the last {hours} hours.")
        return

    print(f"Top consumers: last {hours} hours")
    print()
    header = (
        f"{'Name':<25} {'AvgCPU':>7} {'MaxCPU':>7}"
        f" {'AvgRSS':>8} {'MaxRSS':>8} {'Seen':>5}"
    )
    print(header)
    print("-" * 64)
    for name, avg_cpu, max_cpu, avg_rss, max_rss, appearances in processes:
        print(
            f"{name:<25} {avg_cpu:>6.1f}% {max_cpu:>6.1f}% "
            f"{format_bytes_as_megabytes(int(avg_rss)):>8} "
            f"{format_bytes_as_megabytes(int(max_rss)):>8} "
            f"{appearances:>5}"
        )


def show_database_statistics(connection: sqlite3.Connection) -> None:
    total_snapshots = connection.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
    total_records = connection.execute(
        "SELECT COUNT(*) FROM process_metrics"
    ).fetchone()[0]

    if total_snapshots == 0:
        print("Database is empty.")
        return

    oldest = connection.execute(
        "SELECT MIN(timestamp_epoch) FROM snapshots"
    ).fetchone()[0]
    newest = connection.execute(
        "SELECT MAX(timestamp_epoch) FROM snapshots"
    ).fetchone()[0]

    db_size_bytes = DATABASE_PATH.stat().st_size

    print(f"Database: {DATABASE_PATH}")
    print(f"  Size: {format_bytes_as_megabytes(db_size_bytes)}")
    print(f"  Snapshots: {total_snapshots}")
    print(f"  Process records: {total_records}")
    print(f"  Oldest: {format_epoch_as_local_datetime(oldest)}")
    print(f"  Newest: {format_epoch_as_local_datetime(newest)}")
    print(f"  Span: {(newest - oldest) / 86400:.1f} days")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Sophos monitoring metrics")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("latest", help="Show latest snapshot")

    timeline_parser = subparsers.add_parser("timeline", help="Show timeline summary")
    timeline_parser.add_argument(
        "--hours", type=int, default=24, help="Hours to look back (default: 24)"
    )

    top_parser = subparsers.add_parser("top", help="Show top consumers by average")
    top_parser.add_argument(
        "--hours", type=int, default=24, help="Hours to look back (default: 24)"
    )

    subparsers.add_parser("stats", help="Show database statistics")

    args = parser.parse_args()

    if not DATABASE_PATH.exists():
        print(f"Database not found at {DATABASE_PATH}")
        print("The monitoring service may not have run yet.")
        sys.exit(1)

    connection = sqlite3.connect(str(DATABASE_PATH))
    try:
        if args.command == "latest":
            show_latest_snapshot(connection)
        elif args.command == "timeline":
            show_timeline_summary(connection, args.hours)
        elif args.command == "top":
            show_top_consumers(connection, args.hours)
        elif args.command == "stats":
            show_database_statistics(connection)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
