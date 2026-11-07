from evaluation_suite_support import every_authored_case
from instructions.instruction_surface_scanner import REPO_ROOT

MINIMUM_REFERENCED_PATHS = 50


def referenced_instruction_paths():
    return [
        (suite_path.name, case["nome"], path)
        for suite_path, case in every_authored_case()
        for path in [case.get("instrucao"), *case.get("instrucoes_extras", [])]
        if path
    ]


def test_every_referenced_instruction_path_or_glob_matches_repository_files():
    unresolved = [
        f"{suite}:{name} -> {path}"
        for suite, name, path in referenced_instruction_paths()
        if not any(REPO_ROOT.glob(path))
    ]
    assert not unresolved, (
        "these cases point at instruction files that no longer exist, so the case "
        "would grade ambient context instead of the rule: " + ", ".join(unresolved)
    )


def test_the_instruction_path_scan_covers_the_suites():
    assert len(referenced_instruction_paths()) > MINIMUM_REFERENCED_PATHS


def test_held_out_flags_are_booleans():
    invalid = [
        f"{suite_path.name}:{case['nome']}"
        for suite_path, case in every_authored_case()
        if "reservado" in case and not isinstance(case["reservado"], bool)
    ]
    assert not invalid, f"reservado must be true or false: {invalid}"
