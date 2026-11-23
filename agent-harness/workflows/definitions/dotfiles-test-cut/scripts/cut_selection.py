import argparse
import ast
import json
from pathlib import Path

from apply_cut import named_definition

SILENT = "fails for no mutant of the code it runs"
DOMINATED = "one staying test in the same file catches every mutant it catches"


def kills_by_test(matrix):
    kills = {}
    for record in matrix["mutants"]:
        for name in record["killed_by"]:
            kills.setdefault(name, set()).add(record["mutant"])
    return kills


def reached_tests(matrix):
    return {name for record in matrix["mutants"] for name in record["reached_by"]}


def file_of(name):
    return name.split("::")[0]


def dominator(kills, name, kept):
    return next(
        (
            other
            for other in kept
            if file_of(other) == file_of(name) and kills[other] >= kills[name]
        ),
        None,
    )


def dominated_tests(kills):
    kept = []
    dominated = {}
    for name in sorted(kills, key=lambda name: (-len(kills[name]), name)):
        stronger = dominator(kills, name, kept)
        if stronger is None:
            kept.append(name)
        else:
            dominated[name] = stronger
    return dominated


def definition_source(root, name):
    file_name, *qualified_name = name.split("::")
    text = (root / file_name).read_text()
    node = named_definition(ast.parse(text), qualified_name)
    return "" if node is None else ast.get_source_segment(text, node)


def candidates(root, matrix):
    kills = kills_by_test(matrix)
    silent = [
        {"test": name, "evidence": SILENT, "source": definition_source(root, name)}
        for name in sorted(reached_tests(matrix) - kills.keys())
    ]
    dominated = [
        {
            "test": name,
            "evidence": DOMINATED,
            "source": definition_source(root, name),
            "stronger_test": stronger,
            "stronger_source": definition_source(root, stronger),
        }
        for name, stronger in sorted(dominated_tests(kills).items())
    ]
    return silent + dominated


def arguments():
    parser = argparse.ArgumentParser(
        description="List the measured tests that catch nothing, or nothing one neighbor misses"
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main():
    options = arguments()
    matrix = json.loads(options.matrix.read_text())
    found = candidates(options.root.resolve(), matrix)
    options.output.write_text(json.dumps(found, indent=1) + "\n")
    print(
        json.dumps(
            {
                "candidates_path": str(options.output),
                "candidates": len(found),
                "tests": len(matrix["tests"]),
                "unreached": len(set(matrix["tests"]) - reached_tests(matrix)),
                "mutants": len(matrix["mutants"]),
                "mutants_killed": sum(
                    1 for record in matrix["mutants"] if record["killed_by"]
                ),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
