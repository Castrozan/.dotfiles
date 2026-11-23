import argparse
import ast
import json
from pathlib import Path


def kill_counts(matrix):
    counts = dict.fromkeys(matrix["tests"], 0)
    for mutant in matrix["mutants"]:
        for test in mutant["killed_by"]:
            counts[test] = counts.get(test, 0) + 1
    return counts


def named_definition(tree, qualified_name):
    scope = tree
    for name in qualified_name:
        scope = next(
            (
                node
                for node in scope.body
                if isinstance(
                    node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                )
                and node.name == name
            ),
            None,
        )
        if scope is None:
            return None
    return scope


def definition_source(root, test):
    file_name, *qualified_name = test.split("::")
    text = (root / file_name).read_text()
    node = named_definition(ast.parse(text), qualified_name)
    return "" if node is None else ast.get_source_segment(text, node)


def candidates(root, matrix, maximum_candidates):
    silent = sorted(test for test, count in kill_counts(matrix).items() if count == 0)
    return [
        {"test": test, "source": definition_source(root, test)}
        for test in silent[:maximum_candidates]
    ]


def arguments():
    parser = argparse.ArgumentParser(
        description="List the unit tests that failed for no mutant of their subtree"
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--maximum-candidates", type=int, default=60)
    return parser.parse_args()


def main():
    options = arguments()
    matrix = json.loads(options.matrix.read_text())
    selected = candidates(options.root.resolve(), matrix, options.maximum_candidates)
    killed = sum(1 for mutant in matrix["mutants"] if mutant["killed_by"])
    options.output.write_text(json.dumps(selected, indent=1) + "\n")
    print(
        json.dumps(
            {
                "candidates_path": str(options.output),
                "candidate_count": len(selected),
                "tests": len(matrix["tests"]),
                "mutants": len(matrix["mutants"]),
                "mutants_killed": killed,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
