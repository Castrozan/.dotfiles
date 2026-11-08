import argparse
import contextlib
import copy
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CallObservation:
    outcome: str
    value: str
    printed: str


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="swarm-differential-check",
        description="Call the same functions on a Python module at a git revision and in the working tree, and report any difference in return value, raised exception or printed output.",
    )
    parser.add_argument(
        "--path",
        required=True,
        type=Path,
        help="Module file, relative to --repository.",
    )
    parser.add_argument(
        "--cases",
        required=True,
        type=Path,
        help='JSON list of calls, e.g. [{"function": "parse", "args": ["x"], "kwargs": {}}].',
    )
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    return parser.parse_args()


def module_source_at_revision(repository, revision, relative_path):
    return subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "show",
            f"{revision}:{relative_path.as_posix()}",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    ).stdout


def load_module(module_name, module_path):
    specification = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


def observe_call(module, case):
    printed_output = io.StringIO()
    function = getattr(module, case["function"], None)
    if function is None:
        return CallObservation("missing", case["function"], "")
    try:
        with contextlib.redirect_stdout(printed_output):
            value = function(
                *copy.deepcopy(case.get("args", [])),
                **copy.deepcopy(case.get("kwargs", {})),
            )
    except Exception as raised:
        return CallObservation(
            "raised", f"{type(raised).__name__}: {raised}", printed_output.getvalue()
        )
    return CallObservation("returned", repr(value), printed_output.getvalue())


def main():
    arguments = parse_arguments()
    repository = arguments.repository.resolve()
    refactored_path = repository / arguments.path
    cases = json.loads(arguments.cases.read_text())
    sys.path.insert(0, str(refactored_path.parent))
    with tempfile.TemporaryDirectory(
        prefix="swarm-differential-"
    ) as temporary_directory:
        original_path = Path(temporary_directory) / refactored_path.name
        original_path.write_text(
            module_source_at_revision(repository, arguments.revision, arguments.path)
        )
        original_module = load_module(
            f"swarm_original_{refactored_path.stem}", original_path
        )
        refactored_module = load_module(
            f"swarm_refactored_{refactored_path.stem}", refactored_path
        )
        mismatches = [
            (case, original, refactored)
            for case in cases
            for original, refactored in [
                (
                    observe_call(original_module, case),
                    observe_call(refactored_module, case),
                )
            ]
            if original != refactored
        ]
    for case, original, refactored in mismatches:
        print(
            f"MISMATCH {json.dumps(case)}\n  {arguments.revision}: {original}\n  working tree: {refactored}"
        )
    print(f"{len(cases) - len(mismatches)} of {len(cases)} cases behave identically")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
