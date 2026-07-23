from instruction_surface_scanner import (
    MAXIMUM_SKILL_DESCRIPTION_LENGTH,
    REPO_ROOT,
    every_linted_markdown_file,
    frontmatter_key_values,
    instruction_surface_files,
    repository_path_references,
    sibling_chapter_references,
    skill_chapter_files,
    skill_definition_files,
    unclosed_code_fence_count,
    unresolved_repository_paths,
    unresolved_sibling_chapters,
    xml_tag_structure_error,
)


def test_every_skill_declares_frontmatter_naming_its_own_directory():
    for skill_file in skill_definition_files():
        key_values = frontmatter_key_values(skill_file.read_text())
        relative = skill_file.relative_to(REPO_ROOT)
        assert key_values is not None, (
            f"{relative} has no single-line-per-key frontmatter block"
        )
        assert key_values.get("name") == skill_file.parent.name, (
            f"{relative} declares name '{key_values.get('name')}' "
            f"but lives in directory '{skill_file.parent.name}'"
        )


def test_every_skill_description_is_populated_and_within_the_discovery_limit():
    for skill_file in skill_definition_files():
        key_values = frontmatter_key_values(skill_file.read_text())
        description = (key_values or {}).get("description", "")
        relative = skill_file.relative_to(REPO_ROOT)
        assert description, f"{relative} has no description, so it cannot be routed to"
        assert len(description) <= MAXIMUM_SKILL_DESCRIPTION_LENGTH, (
            f"{relative} description is {len(description)} characters, "
            f"past the {MAXIMUM_SKILL_DESCRIPTION_LENGTH} character discovery limit"
        )


def test_skill_names_are_unique_across_the_skill_tree():
    names_to_files = {}
    for skill_file in skill_definition_files():
        name = (frontmatter_key_values(skill_file.read_text()) or {}).get("name")
        names_to_files.setdefault(name, []).append(
            str(skill_file.relative_to(REPO_ROOT))
        )
    collisions = {
        name: files for name, files in names_to_files.items() if len(files) > 1
    }
    assert not collisions, f"skill names collide, so routing is ambiguous: {collisions}"


def test_xml_instruction_tags_are_balanced_and_correctly_nested():
    for path in instruction_surface_files() + skill_definition_files():
        error = xml_tag_structure_error(path.read_text())
        assert error is None, f"{path.relative_to(REPO_ROOT)} has {error}"


def test_the_xml_tag_checker_rejects_unbalanced_and_crossed_tags():
    assert xml_tag_structure_error("<one>\nbody\n</one>\n") is None
    assert xml_tag_structure_error("<one>\nbody\n") is not None
    assert xml_tag_structure_error("<one>\n<two>\n</one>\n</two>\n") is not None
    assert xml_tag_structure_error("</one>\n") is not None


def test_backticked_repository_paths_in_instruction_surfaces_resolve():
    for path in every_linted_markdown_file():
        unresolved = unresolved_repository_paths(path)
        assert not unresolved, (
            f"{path.relative_to(REPO_ROOT)} points at repository paths "
            f"that no longer exist: {unresolved}"
        )


def test_backticked_sibling_chapter_files_in_skills_resolve():
    for path in skill_definition_files() + skill_chapter_files():
        unresolved = unresolved_sibling_chapters(path)
        assert not unresolved, (
            f"{path.relative_to(REPO_ROOT)} points at sibling chapter files "
            f"that do not exist: {unresolved}"
        )


def test_markdown_code_fences_are_closed():
    for path in every_linted_markdown_file():
        assert unclosed_code_fence_count(path.read_text()) == 0, (
            f"{path.relative_to(REPO_ROOT)} has an odd number of code fence markers, "
            f"so one fence never closes"
        )


def test_the_instruction_surface_scan_covers_the_repository():
    assert len(skill_definition_files()) > 20
    assert len(instruction_surface_files()) > 3
    assert len(skill_chapter_files()) > 20


def test_the_reference_lint_actually_inspects_references():
    repository_references = sum(
        len(repository_path_references(path)) for path in every_linted_markdown_file()
    )
    chapter_references = sum(
        len(sibling_chapter_references(path))
        for path in skill_definition_files() + skill_chapter_files()
    )
    assert repository_references > 5, (
        "the repository path lint found nothing to check, so it passes vacuously"
    )
    assert chapter_references > 10, (
        "the sibling chapter lint found nothing to check, so it passes vacuously"
    )
