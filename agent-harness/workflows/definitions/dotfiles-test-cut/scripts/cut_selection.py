import argparse
import json
from pathlib import Path

SILENT = {
    "condition": 1,
    "reason": "fails for no mutant of the code it runs",
}
REDUNDANT = {
    "condition": 6,
    "reason": "every mutant it catches is caught by a test that stays",
}


def kills_by_test(matrix):
    kills = {}
    for record in matrix["mutants"]:
        for name in record["killed_by"]:
            kills.setdefault(name, set()).add(record["mutant"])
    return kills


def reached_tests(matrix):
    return {name for record in matrix["mutants"] for name in record["reached_by"]}


def smallest_cover(kills):
    uncovered = set().union(*kills.values()) if kills else set()
    kept = set()
    while uncovered:
        best = max(sorted(kills), key=lambda name: len(kills[name] & uncovered))
        kept.add(best)
        uncovered -= kills[best]
    return kept


def selection(matrix):
    kills = kills_by_test(matrix)
    kept = smallest_cover(kills)
    silent = sorted(reached_tests(matrix) - kills.keys())
    redundant = sorted(kills.keys() - kept)
    return {
        "tests": len(matrix["tests"]),
        "unreached": len(set(matrix["tests"]) - reached_tests(matrix)),
        "kept_for_a_kill": len(kept),
        "mutants": len(matrix["mutants"]),
        "mutants_killed": sum(1 for record in matrix["mutants"] if record["killed_by"]),
        "cuts": [{"test": name} | SILENT for name in silent]
        + [{"test": name} | REDUNDANT for name in redundant],
    }


def arguments():
    parser = argparse.ArgumentParser(
        description="Select the measured tests that catch nothing or nothing of their own"
    )
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main():
    options = arguments()
    selected = selection(json.loads(options.matrix.read_text()))
    options.output.write_text(json.dumps(selected, indent=1) + "\n")
    summary = {key: value for key, value in selected.items() if key != "cuts"}
    print(
        json.dumps(
            summary
            | {"selection_path": str(options.output), "cut": len(selected["cuts"])}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
