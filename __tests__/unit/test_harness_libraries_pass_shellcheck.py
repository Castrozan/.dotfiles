import pathlib
import shutil
import subprocess

import pytest

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parent.parent
HARNESS_LIBRARY_DIRECTORY = HARNESS_TESTS_ROOT / "lib"


def harness_library_files() -> list[pathlib.Path]:
    return sorted(HARNESS_LIBRARY_DIRECTORY.glob("*.sh"))


def test_the_harness_libraries_are_discovered():
    assert len(harness_library_files()) > 5, (
        "the harness library directory is empty, so the shellcheck gate below "
        "would pass without inspecting anything"
    )


def test_every_harness_library_passes_shellcheck():
    shellcheck = shutil.which("shellcheck")
    if shellcheck is None:
        pytest.skip("shellcheck unavailable")

    failures = []
    for library in harness_library_files():
        completed = subprocess.run(
            [shellcheck, "--external-sources", "--shell=bash", str(library)],
            capture_output=True,
            text=True,
            cwd=HARNESS_TESTS_ROOT,
        )
        if completed.returncode != 0:
            failures.append(f"{library.name}:\n{completed.stdout}")

    assert not failures, (
        "the test harness itself must pass the same shellcheck gate it enforces on "
        "every other script in the repo:\n" + "\n".join(failures)
    )
