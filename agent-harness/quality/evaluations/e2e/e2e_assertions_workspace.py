import ast
import io
import subprocess
import tokenize
from pathlib import Path

from e2e_models import E2eAssertionResult

DOCSTRING_OWNING_NODE_TYPES = (
    ast.Module,
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
)


def python_comment_violations(source: str) -> list[tuple[int, str]]:
    violations = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        if token.start[0] == 1 and token.string.startswith("#!"):
            continue
        violations.append((token.start[0], f"comment on line {token.start[0]}"))
    return violations


def python_docstring_violations(parsed_module: ast.Module) -> list[tuple[int, str]]:
    violations = []
    for node in ast.walk(parsed_module):
        if not isinstance(node, DOCSTRING_OWNING_NODE_TYPES):
            continue
        if not node.body:
            continue
        first_statement = node.body[0]
        if not isinstance(first_statement, ast.Expr):
            continue
        if not isinstance(first_statement.value, ast.Constant):
            continue
        if not isinstance(first_statement.value.value, str):
            continue
        line_number = first_statement.lineno
        violations.append((line_number, f"docstring on line {line_number}"))
    return violations


def check_python_source_has_no_comments(name: str, source: str) -> E2eAssertionResult:
    try:
        violations = python_comment_violations(source)
        violations += python_docstring_violations(ast.parse(source))
    except (tokenize.TokenError, SyntaxError):
        return E2eAssertionResult(
            name=name, passed=False, detail="file could not be parsed"
        )

    violations.sort()
    if not violations:
        return E2eAssertionResult(name=name, passed=True, detail="no comments found")
    return E2eAssertionResult(
        name=name,
        passed=False,
        detail=f"found: {[description for _, description in violations]}",
    )


def check_non_python_source_has_no_comments(
    name: str, content: str
) -> E2eAssertionResult:
    comment_patterns = ["# ", "// ", "/* ", "# TODO", "# FIXME"]
    found_comments = [pattern for pattern in comment_patterns if pattern in content]
    if not found_comments:
        return E2eAssertionResult(name=name, passed=True, detail="no comments found")

    shebang_only = (
        found_comments == ["# "]
        and content.startswith("#!")
        and content.count("# ") == 1
    )
    if shebang_only:
        return E2eAssertionResult(name=name, passed=True, detail="only shebang line")

    return E2eAssertionResult(
        name=name, passed=False, detail=f"found: {found_comments}"
    )


def check_workspace_file_no_comments_assertion(
    workspace_directory: Path,
    file_path: str,
) -> E2eAssertionResult:
    name = f"{file_path} has no comments"
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return E2eAssertionResult(name=name, passed=False, detail="file does not exist")

    content = full_path.read_text()
    if file_path.endswith(".py"):
        return check_python_source_has_no_comments(name, content)
    return check_non_python_source_has_no_comments(name, content)


def check_workspace_file_changed_assertion(
    workspace_directory: Path,
    file_path: str,
) -> E2eAssertionResult:
    try:
        initial_commit_result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        initial_sha = initial_commit_result.stdout.strip().split("\n")[0]

        diff_result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                initial_sha,
                "HEAD",
            ],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        committed_changes = diff_result.stdout.strip().split("\n")

        uncommitted_result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=5,
        )
        uncommitted = uncommitted_result.stdout.strip().split("\n")

        all_changed = set(committed_changes + uncommitted)
        was_changed = file_path in all_changed
        return E2eAssertionResult(
            name=f"{file_path} was modified",
            passed=was_changed,
            detail=(
                "file was modified"
                if was_changed
                else f"unchanged. Changed: {list(all_changed)}"
            ),
        )
    except Exception:
        return E2eAssertionResult(
            name=f"{file_path} was modified",
            passed=False,
            detail="could not check git status",
        )


def check_workspace_formatted_correctly_assertion(
    workspace_directory: Path,
    file_path: str,
) -> E2eAssertionResult:
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return E2eAssertionResult(
            name=f"{file_path} is formatted",
            passed=False,
            detail="file does not exist",
        )

    if file_path.endswith(".py"):
        result = subprocess.run(
            ["ruff", "check", "--select=E,F,W", str(full_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        passed = result.returncode == 0
        return E2eAssertionResult(
            name=f"{file_path} is formatted",
            passed=passed,
            detail=(
                "ruff check passed" if passed else f"ruff errors: {result.stdout[:200]}"
            ),
        )

    return E2eAssertionResult(
        name=f"{file_path} is formatted",
        passed=True,
        detail="no formatter check available",
    )
