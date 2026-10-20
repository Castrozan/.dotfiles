from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import clean_per_user_temporary_directory


def resolve_reported_directory(reported_directory: str) -> Path:
    with patch("clean_per_user_temporary_directory.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=f"{reported_directory}\n")
        return clean_per_user_temporary_directory.resolve_per_user_temporary_directory()


@pytest.mark.parametrize(
    "reported_directory", ["/private/tmp/", "/Users/user/", "/var/folders/ab/cd/C/"]
)
def test_refuses_a_temporary_directory_outside_per_user_var_folders(reported_directory):
    with pytest.raises(ValueError, match="refusing to clean"):
        resolve_reported_directory(reported_directory)


def test_accepts_the_per_user_var_folders_temporary_directory():
    reported_directory = "/var/folders/xy/abcdefghijklmnopqrstuvwxyz0000gn/T/"

    assert resolve_reported_directory(reported_directory) == Path(reported_directory)
