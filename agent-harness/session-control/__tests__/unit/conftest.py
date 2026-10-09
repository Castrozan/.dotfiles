import pytest

from codex_migration_fixture import prepare_migration
from codex_migration_process_fixture import prepare_process_inspection


@pytest.fixture
def prepared_migration(tmp_path, monkeypatch):
    return prepare_migration(tmp_path, monkeypatch)


@pytest.fixture
def process_inspection(tmp_path, monkeypatch):
    with prepare_process_inspection(tmp_path, monkeypatch) as inspection:
        yield inspection
