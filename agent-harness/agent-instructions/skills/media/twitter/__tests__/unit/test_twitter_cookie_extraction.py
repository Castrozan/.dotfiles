import importlib.util
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest


@pytest.fixture
def extractor(monkeypatch, tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts" / "extract-x-cookies.py"
    specification = importlib.util.spec_from_file_location("cookie_extractor", script)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    temporary_directory = tmp_path / "temporary"
    temporary_directory.mkdir()
    monkeypatch.setattr(module.tempfile, "tempdir", str(temporary_directory))
    return module, temporary_directory


@pytest.fixture
def cookie_database(tmp_path):
    database = tmp_path / "Cookies"
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "CREATE TABLE cookies (name TEXT, value TEXT, host_key TEXT)"
        )
        connection.executemany(
            "INSERT INTO cookies VALUES (?, ?, ?)",
            [
                ("auth_token", "fixture-token", ".x.com"),
                ("ct0", "fixture-csrf", "twitter.com"),
                ("preferences", "fixture-preferences", "mobile.x.com"),
                ("empty", "", ".x.com"),
                ("foreign", "fixture-foreign", "example.test"),
            ],
        )
        connection.commit()
    database.chmod(0o644)
    return database


def test_cookie_copy_is_private_and_removed(extractor, cookie_database, monkeypatch):
    module, temporary_directory = extractor
    connect = sqlite3.connect
    observed_paths = []

    def inspect_connection(database):
        observed_paths.append(Path(database))
        assert Path(database).stat().st_mode & 0o777 == 0o600
        return connect(database)

    monkeypatch.setattr(module.sqlite3, "connect", inspect_connection)
    assert module.extract_x_cookies_from_database(cookie_database) == {
        "auth_token": "fixture-token",
        "ct0": "fixture-csrf",
        "preferences": "fixture-preferences",
    }
    assert observed_paths
    assert all(not path.exists() for path in observed_paths)
    assert not list(temporary_directory.iterdir())


def test_cookie_copy_cannot_overwrite_precreated_symlink(
    extractor, cookie_database, monkeypatch, tmp_path
):
    module, temporary_directory = extractor
    victim = tmp_path / "victim"
    victim.write_text("untouched")
    predicted_path = temporary_directory / "predicted.db"
    predicted_path.symlink_to(victim)
    monkeypatch.setattr(
        module.tempfile, "mktemp", lambda **arguments: str(predicted_path)
    )
    module.extract_x_cookies_from_database(cookie_database)
    assert victim.read_bytes() == b"untouched"
    assert predicted_path.is_symlink()


def test_invalid_database_closes_connection_and_removes_copy(
    extractor, monkeypatch, tmp_path
):
    module, temporary_directory = extractor
    database = tmp_path / "empty.db"
    with closing(sqlite3.connect(database)):
        pass
    connect = sqlite3.connect
    connections = []

    def record_connection(path):
        connection = connect(path)
        connections.append(connection)
        return connection

    monkeypatch.setattr(module.sqlite3, "connect", record_connection)
    with pytest.raises(sqlite3.OperationalError, match="no such table"):
        module.extract_x_cookies_from_database(database)
    assert not list(temporary_directory.iterdir())
    assert len(connections) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connections[0].execute("SELECT 1")


def test_missing_database_leaves_no_copy(extractor, tmp_path):
    module, temporary_directory = extractor
    with pytest.raises(FileNotFoundError):
        module.extract_x_cookies_from_database(tmp_path / "missing")
    assert not list(temporary_directory.iterdir())
