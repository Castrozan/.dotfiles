import argparse
import ast
import json
import sys
from pathlib import Path

from cut_candidates import named_definition

BUDGET_PATH = "repository/verification/quality/test-budget/budget.json"
TEST_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


def first_line(node):
    return min([node.lineno, *[decorator.lineno for decorator in node.decorator_list]])


def without_node(text, node):
    lines = text.split("\n")
    return "\n".join(lines[: first_line(node) - 1] + lines[node.end_lineno :])


def holds_no_statement_but(owner, node):
    return isinstance(owner, ast.ClassDef) and owner.body == [node]


def removal_target(tree, qualified_name):
    node = named_definition(tree, qualified_name)
    if node is None or len(qualified_name) == 1:
        return node
    owner = named_definition(tree, qualified_name[:-1])
    return owner if holds_no_statement_but(owner, node) else node


def still_holds_a_test(text):
    return any(
        isinstance(node, TEST_NODES) and node.name.startswith("test_")
        for node in ast.walk(ast.parse(text))
    )


def remove_test(root, test):
    file_name, *qualified_name = test.split("::")
    path = root / file_name
    text = path.read_text()
    target = removal_target(ast.parse(text), qualified_name)
    if target is None:
        return False
    remaining = without_node(text, target)
    if still_holds_a_test(remaining):
        path.write_text(remaining)
    else:
        path.unlink()
    return True


def lower_budget(root, removed_count):
    budget_path = root / BUDGET_PATH
    budget = json.loads(budget_path.read_text())
    budget["pytest"] -= removed_count
    budget_path.write_text(json.dumps(budget) + "\n")


def apply_cut(root, allowed_tests, requested_cuts):
    removed = []
    refused = []
    for cut in requested_cuts:
        if cut["test"] in allowed_tests and remove_test(root, cut["test"]):
            removed.append(cut)
        else:
            refused.append(cut["test"])
    lower_budget(root, len(removed))
    return {"removed": removed, "refused": refused}


def arguments():
    parser = argparse.ArgumentParser(
        description="Delete the judged tests that were measured candidates and lower the test budget"
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    return parser.parse_args()


def main():
    options = arguments()
    allowed_tests = {
        candidate["test"] for candidate in json.loads(options.candidates.read_text())
    }
    requested_cuts = json.loads(sys.stdin.read())["cuts"]
    print(json.dumps(apply_cut(options.root.resolve(), allowed_tests, requested_cuts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
