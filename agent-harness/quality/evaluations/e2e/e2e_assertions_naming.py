import ast
import re
from pathlib import Path

from e2e_models import E2eAssertionResult

ABBREVIATIONS_WITH_NO_STANDALONE_MEANING = {
    "addr",
    "arr",
    "attr",
    "btn",
    "buf",
    "calc",
    "cfg",
    "cnt",
    "ctx",
    "curr",
    "dst",
    "elem",
    "err",
    "fmt",
    "fn",
    "idx",
    "impl",
    "lst",
    "mgr",
    "msg",
    "obj",
    "prev",
    "ptr",
    "qty",
    "recv",
    "req",
    "resp",
    "svc",
    "sz",
    "tmp",
    "txt",
    "usr",
}

IDENTIFIERS_THE_AUTHOR_CANNOT_CHOOSE = {"self", "cls", "tmp_path"}

SHORTEST_LANGUAGE_MANDATED_DUNDER_BODY = 2

LOWERCASE_TO_UPPERCASE_BOUNDARY_PATTERN = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
UPPERCASE_RUN_TO_CAPITALIZED_WORD_BOUNDARY_PATTERN = re.compile(
    r"(?<=[A-Z])(?=[A-Z][a-z])"
)


def identifier_is_a_discard(identifier: str) -> bool:
    return identifier.strip("_") == ""


def identifier_is_language_mandated_dunder(identifier: str) -> bool:
    if not (identifier.startswith("__") and identifier.endswith("__")):
        return False
    return len(identifier.strip("_")) >= SHORTEST_LANGUAGE_MANDATED_DUNDER_BODY


def bound_identifiers_in_module(parsed_module: ast.Module) -> set[str]:
    bound_identifiers = set()
    for node in ast.walk(parsed_module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound_identifiers.add(node.name)
        elif isinstance(node, ast.arg):
            bound_identifiers.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound_identifiers.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            bound_identifiers.add(node.attr)
        elif isinstance(node, ast.ExceptHandler) and node.name is not None:
            bound_identifiers.add(node.name)
        elif isinstance(node, ast.alias) and node.asname is not None:
            bound_identifiers.add(node.asname)
    return {
        identifier
        for identifier in bound_identifiers
        if identifier not in IDENTIFIERS_THE_AUTHOR_CANNOT_CHOOSE
        and not identifier_is_a_discard(identifier)
        and not identifier_is_language_mandated_dunder(identifier)
    }


def words_in_identifier(identifier: str) -> list[str]:
    words = []
    for underscore_separated_part in identifier.split("_"):
        if not underscore_separated_part:
            continue
        marked_boundaries = LOWERCASE_TO_UPPERCASE_BOUNDARY_PATTERN.sub(
            "_", underscore_separated_part
        )
        marked_boundaries = UPPERCASE_RUN_TO_CAPITALIZED_WORD_BOUNDARY_PATTERN.sub(
            "_", marked_boundaries
        )
        words.extend(part.lower() for part in marked_boundaries.split("_") if part)
    return words


def identifier_is_single_character_after_stripping_underscores(
    identifier: str,
) -> bool:
    return len(identifier.strip("_")) == 1


def identifier_contains_abbreviation_with_no_standalone_meaning(
    identifier: str,
) -> bool:
    for word in words_in_identifier(identifier):
        if word in ABBREVIATIONS_WITH_NO_STANDALONE_MEANING:
            return True
        if word.endswith("s") and word[:-1] in ABBREVIATIONS_WITH_NO_STANDALONE_MEANING:
            return True
    return False


def identifier_is_not_descriptive(identifier: str) -> bool:
    return identifier_is_single_character_after_stripping_underscores(
        identifier
    ) or identifier_contains_abbreviation_with_no_standalone_meaning(identifier)


def check_workspace_file_descriptive_names_assertion(
    workspace_directory: Path,
    file_path: str,
) -> E2eAssertionResult:
    name = f"{file_path} uses descriptive names"
    full_path = workspace_directory / file_path
    if not full_path.exists():
        return E2eAssertionResult(name=name, passed=False, detail="file does not exist")
    if full_path.suffix != ".py":
        return E2eAssertionResult(
            name=name, passed=True, detail="no name analysis available"
        )

    try:
        parsed_module = ast.parse(full_path.read_text())
    except SyntaxError:
        return E2eAssertionResult(
            name=name, passed=False, detail="file could not be parsed"
        )

    non_descriptive_identifiers = sorted(
        identifier
        for identifier in bound_identifiers_in_module(parsed_module)
        if identifier_is_not_descriptive(identifier)
    )
    if not non_descriptive_identifiers:
        return E2eAssertionResult(
            name=name, passed=True, detail="all bound names are descriptive"
        )
    return E2eAssertionResult(
        name=name,
        passed=False,
        detail=f"not descriptive: {non_descriptive_identifiers}",
    )
