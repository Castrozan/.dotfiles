import sqlite3
import time
from unittest.mock import patch, MagicMock

import pytest

import collect_sophos_metrics as collector


@pytest.fixture
def in_memory_database():
    connection = sqlite3.connect(":memory:")
    collector.initialize_database(connection)
    yield connection
    connection.close()


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    db_path = tmp_path / "metrics.db"
    monkeypatch.setattr(collector, "DATABASE_DIRECTORY", tmp_path)
    monkeypatch.setattr(collector, "DATABASE_PATH", db_path)
    return db_path


class TestInitializeDatabase:
    def test_creates_tables(self, in_memory_database):
        tables = in_memory_database.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "snapshots" in table_names
        assert "process_metrics" in table_names
        assert "schema_version" in table_names

    def test_sets_schema_version(self, in_memory_database):
        version = in_memory_database.execute(
            "SELECT version FROM schema_version"
        ).fetchone()
        assert version[0] == collector.SCHEMA_VERSION

    def test_idempotent_initialization(self, in_memory_database):
        collector.initialize_database(in_memory_database)
        versions = in_memory_database.execute(
            "SELECT COUNT(*) FROM schema_version"
        ).fetchone()
        assert versions[0] == 1


class TestParseCpuTimeToSeconds:
    def test_minutes_and_seconds(self):
        assert collector.parse_cpu_time_to_seconds("05:30") == 330.0

    def test_hours_minutes_seconds(self):
        assert collector.parse_cpu_time_to_seconds("01:30:00") == 5400.0

    def test_days_and_time(self):
        result = collector.parse_cpu_time_to_seconds("2-01:00:00")
        assert result == 2 * 86400 + 3600

    def test_zero_time(self):
        assert collector.parse_cpu_time_to_seconds("00:00") == 0.0

    def test_fractional_seconds(self):
        assert collector.parse_cpu_time_to_seconds("00:30.5") == 30.5


class TestStoreSnapshot:
    def test_stores_snapshot_with_metrics(self, in_memory_database):
        metrics = [
            collector.ProcessMetrics(
                pid=1234,
                name="sophos_threat_detector",
                cpu_percent=10.5,
                memory_percent=2.0,
                resident_set_size_bytes=400 * 1024 * 1024,
                virtual_memory_size_bytes=800 * 1024 * 1024,
                thread_count=12,
                io_read_bytes=1000000,
                io_write_bytes=500000,
                cpu_time_seconds=3600.0,
                state="S",
                start_time_epoch=time.time() - 86400,
            ),
            collector.ProcessMetrics(
                pid=5678,
                name="soapd",
                cpu_percent=1.5,
                memory_percent=0.1,
                resident_set_size_bytes=20 * 1024 * 1024,
                virtual_memory_size_bytes=100 * 1024 * 1024,
                thread_count=4,
                io_read_bytes=200000,
                io_write_bytes=100000,
                cpu_time_seconds=600.0,
                state="S",
                start_time_epoch=time.time() - 86400,
            ),
        ]

        snapshot_id = collector.store_snapshot(in_memory_database, metrics)
        assert snapshot_id is not None

        snapshot = in_memory_database.execute(
            "SELECT process_count, total_cpu_percent FROM snapshots WHERE id = ?",
            (snapshot_id,),
        ).fetchone()
        assert snapshot[0] == 2
        assert snapshot[1] == pytest.approx(12.0)

        process_rows = in_memory_database.execute(
            "SELECT name FROM process_metrics WHERE snapshot_id = ? ORDER BY name",
            (snapshot_id,),
        ).fetchall()
        assert len(process_rows) == 2
        assert process_rows[0][0] == "soapd"
        assert process_rows[1][0] == "sophos_threat_detector"

    def test_stores_total_rss(self, in_memory_database):
        metrics = [
            collector.ProcessMetrics(
                pid=1,
                name="test",
                cpu_percent=0,
                memory_percent=0,
                resident_set_size_bytes=100,
                virtual_memory_size_bytes=200,
                thread_count=1,
                io_read_bytes=0,
                io_write_bytes=0,
                cpu_time_seconds=0,
                state="S",
                start_time_epoch=0,
            ),
        ]

        snapshot_id = collector.store_snapshot(in_memory_database, metrics)
        total_rss = in_memory_database.execute(
            "SELECT total_resident_set_size_bytes FROM snapshots WHERE id = ?",
            (snapshot_id,),
        ).fetchone()[0]
        assert total_rss == 100


class TestPruneOldSnapshots:
    def test_prunes_old_data(self, in_memory_database):
        old_timestamp = time.time() - (100 * 86400)
        in_memory_database.execute(
            "INSERT INTO snapshots (timestamp_epoch, total_resident_set_size_bytes, "
            "total_cpu_percent, process_count) VALUES (?, 100, 1.0, 1)",
            (old_timestamp,),
        )
        old_id = in_memory_database.execute("SELECT last_insert_rowid()").fetchone()[0]
        in_memory_database.execute(
            "INSERT INTO process_metrics (snapshot_id, pid, name, cpu_percent, "
            "memory_percent, resident_set_size_bytes, virtual_memory_size_bytes, "
            "thread_count, io_read_bytes, io_write_bytes, cpu_time_seconds, "
            "state, start_time_epoch) "
            "VALUES (?, 1, 'test', 0, 0, 0, 0, 1, 0, 0, 0, 'S', 0)",
            (old_id,),
        )
        in_memory_database.commit()

        pruned = collector.prune_old_snapshots(in_memory_database, 90)
        assert pruned == 1
        remaining = in_memory_database.execute(
            "SELECT COUNT(*) FROM snapshots"
        ).fetchone()[0]
        assert remaining == 0

    def test_keeps_recent_data(self, in_memory_database):
        recent_timestamp = time.time() - 3600
        in_memory_database.execute(
            "INSERT INTO snapshots (timestamp_epoch, total_resident_set_size_bytes, "
            "total_cpu_percent, process_count) VALUES (?, 100, 1.0, 1)",
            (recent_timestamp,),
        )
        in_memory_database.commit()

        pruned = collector.prune_old_snapshots(in_memory_database, 90)
        assert pruned == 0


class TestCollectSophosProcessMetrics:
    def test_parses_ps_output(self):
        fake_ps_output = (
            " 1234 sophos_threat  10.5  2.0 400000  800000 12 S 01:00:00 "
            "0::/sophos.slice/sophos-spl.service\n"
            " 5678 soapd           1.5  0.1  20000  100000  4 S 00:10:00 "
            "0::/sophos.slice/sophos-spl.service\n"
            "  999 firefox         5.0  3.0 500000  900000  8 S 00:30:00 "
            "0::/user.slice\n"
        )

        mock_result = MagicMock()
        mock_result.stdout = fake_ps_output

        with (
            patch("subprocess.run", return_value=mock_result),
            patch.object(collector, "read_io_bytes_from_proc", return_value=(0, 0)),
            patch.object(collector, "read_start_time_from_proc", return_value=0.0),
        ):
            metrics = collector.collect_sophos_process_metrics()

        assert len(metrics) == 2
        names = [m.name for m in metrics]
        assert "sophos_threat" in names
        assert "soapd" in names
        assert "firefox" not in names

    def test_handles_empty_output(self):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            metrics = collector.collect_sophos_process_metrics()

        assert metrics == []


class TestMainFunction:
    def test_full_collection_cycle(self, temporary_database):
        fake_ps_output = (
            " 1234 sophos_threat  10.5  2.0 400000 800000 12 S 01:00:00 "
            "0::/sophos.slice\n"
        )
        mock_result = MagicMock()
        mock_result.stdout = fake_ps_output

        with (
            patch("subprocess.run", return_value=mock_result),
            patch.object(collector, "read_io_bytes_from_proc", return_value=(0, 0)),
            patch.object(collector, "read_start_time_from_proc", return_value=0.0),
        ):
            collector.main()

        assert temporary_database.exists()
        connection = sqlite3.connect(str(temporary_database))
        count = connection.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
        assert count == 1
        connection.close()

    def test_skips_when_no_sophos_processes(self, temporary_database, capsys):
        mock_result = MagicMock()
        mock_result.stdout = (
            "  999 firefox 5.0 3.0 500000 900000 8 S 00:30:00 0::/user.slice\n"
        )

        with patch("subprocess.run", return_value=mock_result):
            collector.main()

        captured = capsys.readouterr()
        assert "no sophos processes found" in captured.out
