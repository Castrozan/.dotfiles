import importlib.util
import pathlib

VERIFICATION_ROOT = pathlib.Path(__file__).resolve().parents[2]
SUITE_MAP_SCRIPT = VERIFICATION_ROOT / "map-test-suite.py"


def load_suite_map():
    specification = importlib.util.spec_from_file_location(
        "suite_map", SUITE_MAP_SCRIPT
    )
    suite_map = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(suite_map)
    return suite_map


def test_a_tier_counts_the_tests_grouped_into_a_subdirectory(tmp_path):
    suite_map = load_suite_map()
    grouped = tmp_path / "__tests__" / "unit" / "mount_guard"
    grouped.mkdir(parents=True)
    (grouped / "test_mounting.py").write_text("def test_it_mounts():\n    pass\n")
    (grouped / "mounting.bats").write_text("@test 'it mounts' {\n  true\n}\n")

    summary = suite_map.summarize_tier(tmp_path / "__tests__", "unit")

    assert summary == {"bats_blocks": 1, "pytest_functions": 1}, (
        "the suite map counted a tier with a flat glob, so it under-reports every "
        "test file grouped into a subdirectory while the collectors still run them"
    )


def test_lua_suites_are_counted_at_any_depth(tmp_path):
    suite_map = load_suite_map()
    grouped = tmp_path / "__tests__" / "workspace"
    grouped.mkdir(parents=True)
    (grouped / "state_test.lua").write_text("return true\n")

    summary = suite_map.summarize_tests_directory(tmp_path / "__tests__")

    assert summary["lua_test_file_count"] == 1, (
        "the lua collector reaches any depth below __tests__, so a map that globs "
        "flat reports fewer suites than actually run"
    )
