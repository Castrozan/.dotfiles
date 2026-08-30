from ai_instruction_format import unclosed_code_fence_count, xml_tag_structure_error
from ai_instruction_references import (
    repository_path_references,
    skill_reference_references,
    skill_relative_script_references,
    unresolved_repository_paths,
    unresolved_skill_references,
    unresolved_skill_relative_scripts,
)
from instruction_surface_scanner import (
    REPO_ROOT,
    every_linted_markdown_file,
    instruction_surface_files,
    skill_definition_files,
    skill_reference_files,
)


def test_xml_instruction_tags_are_balanced_and_not_nested():
    for path in every_linted_markdown_file():
        error = xml_tag_structure_error(path.read_text())
        assert error is None, f"{path.relative_to(REPO_ROOT)} has {error}"


def test_the_xml_tag_checker_rejects_unbalanced_and_nested_tags():
    assert xml_tag_structure_error("<one>\nbody\n</one>\n") is None
    assert xml_tag_structure_error("<one>\nbody\n") is not None
    assert xml_tag_structure_error("<one>\n<two>\n</two>\n</one>\n") is not None
    assert xml_tag_structure_error("</one>\n") is not None


def test_backticked_repository_paths_in_instruction_surfaces_resolve():
    for path in every_linted_markdown_file():
        unresolved = unresolved_repository_paths(path)
        assert not unresolved, (
            f"{path.relative_to(REPO_ROOT)} points at repository paths "
            f"that no longer exist: {unresolved}"
        )


def test_backticked_skill_reference_files_resolve_from_the_skill_root():
    for path in skill_definition_files() + skill_reference_files():
        unresolved = unresolved_skill_references(path)
        assert not unresolved, (
            f"{path.relative_to(REPO_ROOT)} points at skill references "
            f"that do not exist: {unresolved}"
        )


def test_backticked_skill_relative_scripts_resolve_from_the_skill_root():
    for path in skill_definition_files() + skill_reference_files():
        unresolved = unresolved_skill_relative_scripts(path)
        assert not unresolved, (
            f"{path.relative_to(REPO_ROOT)} tells the agent to run scripts that "
            f"are not packaged with the skill: {unresolved}"
        )


def test_markdown_code_fences_are_closed():
    for path in every_linted_markdown_file():
        assert unclosed_code_fence_count(path.read_text()) == 0, (
            f"{path.relative_to(REPO_ROOT)} has an odd number of code fence markers, "
            f"so one fence never closes"
        )


def test_every_declared_instruction_surface_exists_on_disk():
    missing = [
        str(path.relative_to(REPO_ROOT))
        for path in instruction_surface_files()
        if not path.is_file()
    ]
    assert not missing, (
        "these surfaces are declared for linting but absent, so the lint would "
        f"silently cover less than it claims: {missing}"
    )


def test_the_instruction_surface_scan_covers_the_repository():
    assert len(skill_definition_files()) > 20
    assert len(instruction_surface_files()) > 3
    assert len(skill_reference_files()) > 20


def test_the_reference_lint_actually_inspects_references():
    repository_references = sum(
        len(repository_path_references(path)) for path in every_linted_markdown_file()
    )
    reference_files = sum(
        len(skill_reference_references(path))
        for path in skill_definition_files() + skill_reference_files()
    )
    script_references = sum(
        len(skill_relative_script_references(path))
        for path in skill_definition_files() + skill_reference_files()
    )
    assert repository_references > 5
    assert reference_files > 10
    assert script_references > 2
