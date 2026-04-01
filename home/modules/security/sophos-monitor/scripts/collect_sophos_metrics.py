import os
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

DATABASE_DIRECTORY = Path(
    os.environ.get(
        "SOPHOS_MONITOR_DATA_DIR",
        os.path.expanduser("~/.local/share/sophos-monitor"),
    )
)
DATABASE_PATH = DATABASE_DIRECTORY / "metrics.db"

SCHEMA_VERSION = 1


@dataclass
class ProcessMetrics:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    resident_set_size_bytes: int
    virtual_memory_size_bytes: int
    thread_count: int
    io_read_bytes: int
    io_write_bytes: int
    cpu_time_seconds: float
    state: str
    start_time_epoch: float


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_epoch REAL NOT NULL,
            total_resident_set_size_bytes INTEGER NOT NULL,
            total_cpu_percent REAL NOT NULL,
            process_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS process_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            pid INTEGER NOT NULL,
            name TEXT NOT NULL,
            cpu_percent REAL NOT NULL,
            memory_percent REAL NOT NULL,
            resident_set_size_bytes INTEGER NOT NULL,
            virtual_memory_size_bytes INTEGER NOT NULL,
            thread_count INTEGER NOT NULL,
            io_read_bytes INTEGER NOT NULL,
            io_write_bytes INTEGER NOT NULL,
            cpu_time_seconds REAL NOT NULL,
            state TEXT NOT NULL,
            start_time_epoch REAL NOT NULL,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
        );

        CREATE INDEX IF NOT EXISTS idx_process_metrics_snapshot
            ON process_metrics(snapshot_id);
        CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
            ON snapshots(timestamp_epoch);
    """)

    existing_version = connection.execute(
        "SELECT version FROM schema_version LIMIT 1"
    ).fetchone()
    if existing_version is None:
        connection.execute(
            "INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,)
        )
    connection.commit()


def parse_cpu_time_to_seconds(cpu_time_string: str) -> float:
    total_seconds = 0.0
    if "-" in cpu_time_string:
        days_part, time_part = cpu_time_string.split("-", 1)
        total_seconds += int(days_part) * 86400
        cpu_time_string = time_part

    parts = cpu_time_string.split(":")
    if len(parts) == 3:
        total_seconds += int(parts[0]) * 3600
        total_seconds += int(parts[1]) * 60
        total_seconds += float(parts[2])
    elif len(parts) == 2:
        total_seconds += int(parts[0]) * 60
        total_seconds += float(parts[1])
    return total_seconds


def read_io_bytes_from_proc(pid: int) -> tuple[int, int]:
    try:
        io_path = Path(f"/proc/{pid}/io")
        io_content = io_path.read_text()
        read_bytes = 0
        write_bytes = 0
        for line in io_content.strip().split("\n"):
            key, value = line.split(":", 1)
            if key.strip() == "read_bytes":
                read_bytes = int(value.strip())
            elif key.strip() == "write_bytes":
                write_bytes = int(value.strip())
        return read_bytes, write_bytes
    except (PermissionError, FileNotFoundError, ValueError):
        return 0, 0


def read_start_time_from_proc(pid: int) -> float:
    try:
        stat_path = Path(f"/proc/{pid}/stat")
        stat_content = stat_path.read_text()
        closing_paren_index = stat_content.rfind(")")
        fields_after_comm = stat_content[closing_paren_index + 2 :].split()
        clock_ticks_since_boot = int(fields_after_comm[19])
        with open("/proc/uptime") as uptime_file:
            system_uptime_seconds = float(uptime_file.read().split()[0])
        clock_ticks_per_second = os.sysconf("SC_CLK_TCK")
        process_start_seconds_since_boot = (
            clock_ticks_since_boot / clock_ticks_per_second
        )
        boot_time_epoch = time.time() - system_uptime_seconds
        return boot_time_epoch + process_start_seconds_since_boot
    except (FileNotFoundError, ValueError, IndexError):
        return 0.0


def collect_sophos_process_metrics() -> list[ProcessMetrics]:
    ps_result = subprocess.run(
        [
            "ps",
            "-eo",
            "pid,comm,pcpu,pmem,rss,vsz,nlwp,state,cputime,cgroup",
            "--no-headers",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    metrics = []
    for line in ps_result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        if "sophos" not in line.lower():
            continue

        fields = line.split()
        if len(fields) < 9:
            continue

        pid = int(fields[0])
        name = fields[1]
        cpu_percent = float(fields[2])
        memory_percent = float(fields[3])
        resident_set_size_kb = int(fields[4])
        virtual_memory_size_kb = int(fields[5])
        thread_count = int(fields[6])
        state = fields[7]
        cpu_time_string = fields[8]

        io_read_bytes, io_write_bytes = read_io_bytes_from_proc(pid)
        start_time_epoch = read_start_time_from_proc(pid)

        metrics.append(
            ProcessMetrics(
                pid=pid,
                name=name,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                resident_set_size_bytes=resident_set_size_kb * 1024,
                virtual_memory_size_bytes=virtual_memory_size_kb * 1024,
                thread_count=thread_count,
                io_read_bytes=io_read_bytes,
                io_write_bytes=io_write_bytes,
                cpu_time_seconds=parse_cpu_time_to_seconds(cpu_time_string),
                state=state,
                start_time_epoch=start_time_epoch,
            )
        )

    return metrics


def store_snapshot(
    connection: sqlite3.Connection, metrics: list[ProcessMetrics]
) -> int:
    timestamp = time.time()
    total_rss = sum(m.resident_set_size_bytes for m in metrics)
    total_cpu = sum(m.cpu_percent for m in metrics)

    cursor = connection.execute(
        """INSERT INTO snapshots (timestamp_epoch, total_resident_set_size_bytes,
           total_cpu_percent, process_count) VALUES (?, ?, ?, ?)""",
        (timestamp, total_rss, total_cpu, len(metrics)),
    )
    snapshot_id = cursor.lastrowid

    connection.executemany(
        """INSERT INTO process_metrics (snapshot_id, pid, name, cpu_percent,
           memory_percent, resident_set_size_bytes, virtual_memory_size_bytes,
           thread_count, io_read_bytes, io_write_bytes, cpu_time_seconds,
           state, start_time_epoch)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                snapshot_id,
                m.pid,
                m.name,
                m.cpu_percent,
                m.memory_percent,
                m.resident_set_size_bytes,
                m.virtual_memory_size_bytes,
                m.thread_count,
                m.io_read_bytes,
                m.io_write_bytes,
                m.cpu_time_seconds,
                m.state,
                m.start_time_epoch,
            )
            for m in metrics
        ],
    )

    connection.commit()
    return snapshot_id


def prune_old_snapshots(connection: sqlite3.Connection, retention_days: int) -> int:
    cutoff_epoch = time.time() - (retention_days * 86400)
    old_snapshot_ids = connection.execute(
        "SELECT id FROM snapshots WHERE timestamp_epoch < ?", (cutoff_epoch,)
    ).fetchall()

    if not old_snapshot_ids:
        return 0

    id_list = [row[0] for row in old_snapshot_ids]
    placeholders = ",".join("?" * len(id_list))
    connection.execute(
        f"DELETE FROM process_metrics WHERE snapshot_id IN ({placeholders})", id_list
    )
    connection.execute(f"DELETE FROM snapshots WHERE id IN ({placeholders})", id_list)
    connection.commit()
    return len(id_list)


def print_snapshot_summary(metrics: list[ProcessMetrics], snapshot_id: int) -> None:
    total_rss_megabytes = sum(m.resident_set_size_bytes for m in metrics) / (
        1024 * 1024
    )
    total_cpu = sum(m.cpu_percent for m in metrics)
    print(
        f"[sophos-monitor] snapshot={snapshot_id} "
        f"processes={len(metrics)} "
        f"total_rss={total_rss_megabytes:.0f}MB "
        f"total_cpu={total_cpu:.1f}%"
    )


def main() -> None:
    retention_days = int(os.environ.get("SOPHOS_MONITOR_RETENTION_DAYS", "90"))

    DATABASE_DIRECTORY.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(DATABASE_PATH))
    try:
        initialize_database(connection)

        metrics = collect_sophos_process_metrics()
        if not metrics:
            print("[sophos-monitor] no sophos processes found, skipping snapshot")
            return

        snapshot_id = store_snapshot(connection, metrics)
        print_snapshot_summary(metrics, snapshot_id)

        pruned_count = prune_old_snapshots(connection, retention_days)
        if pruned_count > 0:
            print(f"[sophos-monitor] pruned {pruned_count} old snapshots")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
