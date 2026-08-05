import pathlib
import re

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parents[2]
COLLECTING_DIRECTORIES = (
    HARNESS_TESTS_ROOT / "runner",
    HARNESS_TESTS_ROOT / "cover",
)
SHARED_DISCOVERY_LIBRARY_NAME = "discovery.sh"

RAW_FIND_PATTERN = re.compile(r"(?:^|[\s(;&|`])find\s")
TEST_PATH_MARKERS = ("__tests__", ".bats", "test_", "_test.")


def runner_libraries_that_may_not_collect_by_hand():
    return sorted(
        path
        for directory in COLLECTING_DIRECTORIES
        for path in directory.glob("*.sh")
        if path.name != SHARED_DISCOVERY_LIBRARY_NAME
    )


def test_the_runner_libraries_are_discovered():
    assert len(runner_libraries_that_may_not_collect_by_hand()) > 5, (
        "the runner directory is empty, so the gate below would pass without "
        "inspecting anything"
    )


def logical_lines(shell_source):
    joined = []
    continued = ""
    first_line_number = 1
    for line_number, line in enumerate(shell_source.splitlines(), start=1):
        if not continued:
            first_line_number = line_number
        if line.endswith("\\"):
            continued += line[:-1] + " "
            continue
        joined.append((first_line_number, continued + line))
        continued = ""
    if continued:
        joined.append((first_line_number, continued))
    return joined


def test_no_tier_collects_test_files_with_a_raw_find():
    offenders = []
    for library in runner_libraries_that_may_not_collect_by_hand():
        for line_number, line in logical_lines(library.read_text()):
            if not RAW_FIND_PATTERN.search(line):
                continue
            if any(marker in line for marker in TEST_PATH_MARKERS):
                offenders.append(f"{library.name}:{line_number}: {line.strip()}")

    assert not offenders, (
        "a tier that gathers its own test files with find bypasses "
        f"{SHARED_DISCOVERY_LIBRARY_NAME}, so it ignores the pruned directories and "
        "the foreign-platform roots and ends up running the other platform's suites. "
        "Call _discover_test_files with a path pattern instead. Raw collectors:\n"
        + "\n".join(offenders)
    )
