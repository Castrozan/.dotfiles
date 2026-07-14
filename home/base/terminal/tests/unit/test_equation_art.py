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
    frame_lines = equation_art.render_equation_frame(1.0, columns, rows, "twin").split(
        "\n"
    )
    assert len(frame_lines) == rows
    assert all(len(line) == columns for line in frame_lines)


def test_frame_is_deterministic_for_same_time_size_and_formula():
    first = equation_art.render_equation_frame(2.5, 48, 24, "solo")
    second = equation_art.render_equation_frame(2.5, 48, 24, "solo")
    assert first == second


def test_every_formula_plots_some_braille_points():
    for formula_name in equation_art.list_formula_names():
        frame = equation_art.render_equation_frame(1.0, 60, 30, formula_name)
        assert any(
            ord(character) >= equation_art.BRAILLE_BASE for character in frame
        ), formula_name


def test_frame_advances_over_time():
    early = equation_art.render_equation_frame(0.5, 60, 30, "twin")
    later = equation_art.render_equation_frame(5.0, 60, 30, "twin")
    assert early != later


def test_distinct_formulas_render_differently():
    twin = equation_art.render_equation_frame(3.0, 60, 30, "twin")
    petal = equation_art.render_equation_frame(3.0, 60, 30, "petal")
    assert twin != petal


def test_list_formula_names_matches_registry():
    assert equation_art.list_formula_names() == list(equation_art.EQUATION_FORMULAS)
    assert "twin" in equation_art.list_formula_names()
