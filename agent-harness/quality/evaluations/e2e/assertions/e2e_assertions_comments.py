import ast
import io
import tokenize
from pathlib import Path

from e2e.sessions.e2e_models import E2eAssertionResult

DOCSTRING_OWNING_NODE_TYPES = (
    ast.Module,
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
)

TOOLING_DIRECTIVE_KEYWORDS = {
    "fmt",
    "isort",
    "mypy",
    "noqa",
    "nosec",
    "pragma",
    "pyright",
    "ruff",
    "type",
}

ENCODING_DECLARATION_PREFIX = "-*- coding:"


def comment_is_a_tooling_directive(comment_text: str) -> bool:
    directive_body = comment_text.lstrip("#").strip()
    if directive_body.startswith(ENCODING_DECLARATION_PREFIX):
        return True
    return directive_body.partition(":")[0].strip() in TOOLING_DIRECTIVE_KEYWORDS


def python_comment_violations(source: str) -> list[tuple[int, str]]:
    violations = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if _is_ignored_python_comment(token):
            continue
        violations.append((token.start[0], f"comment on line {token.start[0]}"))
    return violations


def _is_ignored_python_comment(token):
    if token.type != tokenize.COMMENT:
        return True
    if token.start[0] == 1 and token.string.startswith("#!"):
        return True
    return comment_is_a_tooling_directive(token.string)


def python_docstring_violations(parsed_module: ast.Module) -> list[tuple[int, str]]:
    violations = []
    for node in ast.walk(parsed_module):
        if not _is_docstring_owner_with_docstring(node):
            continue
        line_number = node.body[0].lineno
        violations.append((line_number, f"docstring on line {line_number}"))
    return violations


def _is_docstring_owner_with_docstring(node):
    if not isinstance(node, DOCSTRING_OWNING_NODE_TYPES) or not node.body:
        return False
    first_statement = node.body[0]
    if not isinstance(first_statement, ast.Expr):
        return False
    if not isinstance(first_statement.value, ast.Constant):
        return False
    return isinstance(first_statement.value.value, str)


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

    if _contains_only_shebang_comment(found_comments, content):
        return E2eAssertionResult(name=name, passed=True, detail="only shebang line")

    return E2eAssertionResult(
        name=name, passed=False, detail=f"found: {found_comments}"
    )


def _contains_only_shebang_comment(found_comments, content):
    return (
        found_comments == ["# "]
        and content.startswith("#!")
        and content.count("# ") == 1
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
