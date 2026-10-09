import pytest

from exclusive_run_lock_support import (
    build_lock_file_path_for,
    build_unique_lock_name,
)


@pytest.fixture
def unique_lock_name_with_cleanup():
    name = build_unique_lock_name()
    yield name
    build_lock_file_path_for(name).unlink(missing_ok=True)
