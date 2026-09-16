import os
import subprocess
import sys

import coverage


def test_python_startup_does_not_load_coverage_unless_requested():
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COVERAGE_", "COV_CORE_"))
    }
    completed = subprocess.run(
        [sys.executable, "-c", "import sys; print('coverage' in sys.modules)"],
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout == "False\n"


def test_python_child_process_records_only_executed_lines(tmp_path):
    child = tmp_path / "child.py"
    child.write_text(
        "import sys\n"
        "if sys.argv[1] == 'selected':\n"
        "    print('covered branch')\n"
        "else:\n"
        "    print('uncovered branch')\n"
    )
    data_path = tmp_path / ".coverage"
    configuration = tmp_path / "coverage.ini"
    configuration.write_text(
        f"[run]\nsource = {tmp_path}\ndata_file = {data_path}\nparallel = True\n"
    )
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COVERAGE_", "COV_CORE_"))
    }
    environment["COVERAGE_PROCESS_START"] = str(configuration)

    completed = subprocess.run(
        [sys.executable, str(child), "selected"],
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )

    assert completed.stdout == "covered branch\n"
    measurement = coverage.Coverage(data_file=str(data_path))
    measurement.combine(data_paths=[str(tmp_path)])
    executed_lines = measurement.get_data().lines(str(child))
    assert executed_lines is not None
    assert 3 in executed_lines
    assert 5 not in executed_lines
