import ast
import pathlib

SESSION_START_HOOK_DIRECTORY = (
    pathlib.Path(__file__).resolve().parent.parent.parent / "session-start"
)


def _session_start_module_paths():
    return sorted(SESSION_START_HOOK_DIRECTORY.glob("*.py"))


def _module_imports_future_annotations(module_source: str) -> bool:
    parsed_module = ast.parse(module_source)
    for statement in parsed_module.body:
        if isinstance(statement, ast.ImportFrom) and statement.module == "__future__":
            if any(alias.name == "annotations" for alias in statement.names):
                return True
    return False


def test_every_session_start_module_imports_future_annotations():
    modules_missing_future_annotations = []
    for module_path in _session_start_module_paths():
        if not _module_imports_future_annotations(module_path.read_text()):
            modules_missing_future_annotations.append(module_path.name)

    assert modules_missing_future_annotations == [], (
        "macOS ships /usr/bin/python3 as 3.9, and SessionStart hooks can run under it; "
        "every session-start module must 'from __future__ import annotations' so PEP 604 "
        "('str | None') return annotations are not evaluated at definition time and crash. "
        f"Missing in: {modules_missing_future_annotations}"
    )
