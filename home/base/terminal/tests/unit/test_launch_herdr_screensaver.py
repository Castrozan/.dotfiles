import importlib.util
import pathlib
import types

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts"
    / "launch_herdr_screensaver.py"
)


def _load_launcher_module():
    module_spec = importlib.util.spec_from_file_location(
        "launch_herdr_screensaver", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


launcher = _load_launcher_module()


def _which_returning(available_executables):
    available = set(available_executables)

    def fake_which(executable):
        return f"/usr/bin/{executable}" if executable in available else None

    return fake_which


def _list_formulas_returning(formula_names):
    def fake_run(arguments, **_keyword_arguments):
        return types.SimpleNamespace(stdout="\n".join(formula_names) + "\n")

    return fake_run


def test_split_command_keeps_single_command_whole():
    assert launcher.split_command_into_segments("cmatrix -b -u 8") == [
        "cmatrix -b -u 8"
    ]


def test_split_command_separates_on_semicolon():
    assert launcher.split_command_into_segments("sleep 3; bad-apple") == [
        "sleep 3",
        "bad-apple",
    ]


def test_split_command_separates_on_all_shell_operators():
    assert launcher.split_command_into_segments("a && b || c | d & e") == [
        "a",
        "b",
        "c",
        "d",
        "e",
    ]


def test_command_available_when_every_segment_resolves(monkeypatch):
    monkeypatch.setattr(
        launcher.shutil, "which", _which_returning({"sleep", "bad-apple"})
    )
    assert launcher.all_command_segments_available("sleep 3; bad-apple") is True


def test_command_unavailable_when_any_segment_missing(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"sleep"}))
    assert launcher.all_command_segments_available("sleep 3; bad-apple") is False


def test_resolve_prefers_cbonsai_primary_when_present(monkeypatch):
    monkeypatch.setattr(
        launcher.shutil, "which", _which_returning({"cbonsai", "cmatrix"})
    )
    assert launcher.resolve_available_screensaver_commands() == [
        "cbonsai --live --infinite",
        "cmatrix -b -u 8",
    ]


def test_resolve_falls_back_to_cmatrix_primary_when_cbonsai_absent(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"cmatrix"}))
    assert launcher.resolve_available_screensaver_commands() == [
        "cmatrix -b -s -u 8",
        "cmatrix -b -u 8",
    ]


def test_resolve_includes_bad_apple_only_when_all_its_segments_present(monkeypatch):
    monkeypatch.setattr(
        launcher.shutil,
        "which",
        _which_returning({"cbonsai", "cmatrix", "sleep", "bad-apple"}),
    )
    assert launcher.resolve_available_screensaver_commands() == [
        "cbonsai --live --infinite",
        "cmatrix -b -u 8",
        "sleep 3; bad-apple",
    ]


def test_resolve_is_empty_when_nothing_available(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning(set()))
    assert launcher.resolve_available_screensaver_commands() == []


def test_resolve_equation_art_command_picks_a_listed_formula(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"equation-art"}))
    monkeypatch.setattr(
        launcher.subprocess, "run", _list_formulas_returning(["twin", "solo", "swirl"])
    )
    monkeypatch.setattr(launcher.random, "choice", lambda names: names[1])
    assert launcher.resolve_equation_art_command() == "equation-art --formula solo"


def test_resolve_equation_art_command_falls_back_when_binary_absent(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning(set()))
    assert launcher.resolve_equation_art_command() == "equation-art"


def test_resolve_equation_art_command_falls_back_when_listing_fails(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"equation-art"}))

    def raise_oserror(arguments, **_keyword_arguments):
        raise OSError("equation-art not runnable")

    monkeypatch.setattr(launcher.subprocess, "run", raise_oserror)
    assert launcher.resolve_equation_art_command() == "equation-art"


def test_resolve_equation_art_command_falls_back_when_no_formulas_listed(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"equation-art"}))
    monkeypatch.setattr(launcher.subprocess, "run", _list_formulas_returning([]))
    assert launcher.resolve_equation_art_command() == "equation-art"


def test_resolve_lists_randomized_equation_art_first_when_present(monkeypatch):
    monkeypatch.setattr(
        launcher.shutil,
        "which",
        _which_returning({"equation-art", "cbonsai", "cmatrix"}),
    )
    monkeypatch.setattr(
        launcher, "resolve_equation_art_command", lambda: "equation-art --formula petal"
    )
    assert launcher.resolve_available_screensaver_commands() == [
        "equation-art --formula petal",
        "cbonsai --live --infinite",
        "cmatrix -b -u 8",
    ]


def test_wrap_routes_randomized_equation_art_through_precompute_loop(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"precompute-loop"}))
    assert (
        launcher.wrap_command_for_cheap_replay("equation-art --formula swirl")
        == f"precompute-loop --seconds {launcher.PRECOMPUTE_LOOP_CAPTURE_SECONDS} "
        "-- equation-art --formula swirl"
    )


def test_wrap_leaves_incremental_generators_live(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"precompute-loop"}))
    assert (
        launcher.wrap_command_for_cheap_replay("cmatrix -b -u 8") == "cmatrix -b -u 8"
    )
    assert (
        launcher.wrap_command_for_cheap_replay("cbonsai --live --infinite")
        == "cbonsai --live --infinite"
    )


def test_wrap_leaves_command_untouched_when_precompute_loop_absent(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning(set()))
    assert launcher.wrap_command_for_cheap_replay("equation-art") == "equation-art"
