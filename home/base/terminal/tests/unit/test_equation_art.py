import importlib.util
import pathlib

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "equation_art.py"
)


def _load_equation_art_module():
    module_spec = importlib.util.spec_from_file_location("equation_art", SCRIPT_PATH)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


equation_art = _load_equation_art_module()


def test_frame_has_exact_pane_dimensions():
    columns, rows = 60, 30
    frame_lines = equation_art.render_equation_frame(1.0, columns, rows).split("\n")
    assert len(frame_lines) == rows
    assert all(len(line) == columns for line in frame_lines)


def test_frame_is_deterministic_for_same_time_and_size():
    first = equation_art.render_equation_frame(2.5, 48, 24)
    second = equation_art.render_equation_frame(2.5, 48, 24)
    assert first == second


def test_frame_plots_some_braille_points():
    frame = equation_art.render_equation_frame(1.0, 60, 30)
    assert any(character != " " for character in frame)


def test_frame_advances_over_time():
    early = equation_art.render_equation_frame(0.5, 60, 30)
    later = equation_art.render_equation_frame(5.0, 60, 30)
    assert early != later
