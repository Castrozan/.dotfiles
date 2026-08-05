import pathlib

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNNER_DIRECTORY = HARNESS_TESTS_ROOT / "runner"
COVERAGE_DIRECTORY = HARNESS_TESTS_ROOT / "cover"

BUILTINS_ABSENT_FROM_BASH_THREE = ("mapfile", "readarray", "declare -A", "local -A")


def shell_libraries_sourced_without_a_version_guard():
    return sorted([*RUNNER_DIRECTORY.glob("*.sh"), *COVERAGE_DIRECTORY.glob("*.sh")])


def test_the_shell_libraries_are_discovered():
    assert len(shell_libraries_sourced_without_a_version_guard()) > 5, (
        "no shell libraries were found, so the gate below would pass without "
        "inspecting anything"
    )


def test_no_library_depends_on_a_builtin_the_system_bash_lacks():
    offenders = []
    for library in shell_libraries_sourced_without_a_version_guard():
        for line_number, line in enumerate(library.read_text().splitlines(), start=1):
            for builtin in BUILTINS_ABSENT_FROM_BASH_THREE:
                if builtin in line:
                    offenders.append(f"{library.name}:{line_number}: {line.strip()}")

    assert not offenders, (
        "macOS ships bash 3.2 as /bin/bash and the documented way to run one tier is "
        "to source these libraries into whatever bash is on PATH, so a builtin bash 3 "
        "lacks does not raise: the assignment it feeds silently yields an empty file "
        "list, every tier reads that as 'no tests in this tier' and returns success. "
        "A whole tier then reports green having run nothing. Use a portable read loop "
        "instead. Offending lines:\n" + "\n".join(offenders)
    )
