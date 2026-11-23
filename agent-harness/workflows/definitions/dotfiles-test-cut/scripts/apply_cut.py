import argparse
import ast
import json
import subprocess
from pathlib import Path

BUDGET_PATH = "repository/verification/quality/test-budget/budget.json"
DEFINITION_NODES = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
TEST_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
UNUSED_NAME_RULES = "F401,F811,F841"
RUFF_TIMEOUT_SECONDS = 60


def named_definition(tree, qualified_name):
    scope = tree
    for name in qualified_name:
        scope = next(
            (
                node
                for node in scope.body
                if isinstance(node, DEFINITION_NODES) and node.name == name
            ),
            None,
        )
        if scope is None:
            return None
    return scope


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


def tidy(root, tests):
    touched = sorted(
        {test.split("::")[0] for test in tests if (root / test.split("::")[0]).exists()}
    )
    if not touched:
        return
    for command in (
        [
            "ruff",
            "check",
            "--quiet",
            "--select",
            UNUSED_NAME_RULES,
            "--fix",
            "--exit-zero",
        ],
        ["ruff", "format", "--quiet"],
    ):
        subprocess.run(
            [*command, *touched], cwd=root, check=True, timeout=RUFF_TIMEOUT_SECONDS
        )


def apply_cut(root, candidates):
    removed = [name for name in candidates if remove_test(root, name)]
    lower_budget(root, len(removed))
    tidy(root, removed)
    return {"removed": removed, "refused": sorted(set(candidates) - set(removed))}


def arguments():
    parser = argparse.ArgumentParser(
        description="Delete the measured candidates and lower the test budget by their count"
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main():
    options = arguments()
    candidates = [
        candidate["test"] for candidate in json.loads(options.candidates.read_text())
    ]
    applied = apply_cut(options.root.resolve(), candidates)
    options.output.write_text(json.dumps(applied, indent=1) + "\n")
    print(
        json.dumps({"removed": len(applied["removed"]), "refused": applied["refused"]})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
