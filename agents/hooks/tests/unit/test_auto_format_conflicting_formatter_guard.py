import importlib.util
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
AUTO_FORMAT_SCRIPT = next(HOOKS_ROOT.rglob("auto-format.py"))

_spec = importlib.util.spec_from_file_location("auto_format_hook", AUTO_FORMAT_SCRIPT)
auto_format_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(auto_format_hook)


def test_biome_repo_flags_typescript_conflict(tmp_path):
    (tmp_path / "biome.json").write_text("{}")
    typescript_file = tmp_path / "app.ts"
    typescript_file.write_text("const a = 1\n")
    assert (
        auto_format_hook.repository_declares_conflicting_formatter(
            str(typescript_file), ".ts"
        )
        is True
    )


def test_black_repo_flags_python_conflict(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.black]\nline-length = 88\n")
    python_file = tmp_path / "module.py"
    python_file.write_text("value = 1\n")
    assert (
        auto_format_hook.repository_declares_conflicting_formatter(
            str(python_file), ".py"
        )
        is True
    )


def test_ruff_configured_python_repo_is_not_a_conflict(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.black]\n\n[tool.ruff.format]\nquote-style = 'double'\n"
    )
    python_file = tmp_path / "module.py"
    python_file.write_text("value = 1\n")
    assert (
        auto_format_hook.repository_declares_conflicting_formatter(
            str(python_file), ".py"
        )
        is False
    )


def test_plain_repo_has_no_conflict(tmp_path):
    python_file = tmp_path / "module.py"
    python_file.write_text("value = 1\n")
    assert (
        auto_format_hook.repository_declares_conflicting_formatter(
            str(python_file), ".py"
        )
        is False
    )
