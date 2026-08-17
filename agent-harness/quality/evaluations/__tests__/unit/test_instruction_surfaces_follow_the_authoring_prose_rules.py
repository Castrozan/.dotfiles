from instruction_surface_prose import (
    MAXIMUM_INSTRUCTION_LINE_LENGTH,
    over_length_lines,
)
from instruction_surface_scanner import (
    REPO_ROOT,
    VENDORED_DIRECTORY_NAMES,
    every_linted_markdown_file,
)


def test_no_instruction_surface_line_exceeds_the_authoring_wrap():
    offenders = {}
    for path in every_linted_markdown_file():
        over = over_length_lines(path)
        if over:
            offenders[str(path.relative_to(REPO_ROOT))] = over[:3]
    assert not offenders, (
        f"the instructions skill caps an instruction line at "
        f"{MAXIMUM_INSTRUCTION_LINE_LENGTH} characters, wrapped at a word boundary; "
        f"these files carry longer lines (file -> [(line, length)]): {offenders}"
    )


def test_the_prose_lints_ignore_installed_dependency_trees():
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in every_linted_markdown_file()
        if any(part in VENDORED_DIRECTORY_NAMES for part in path.parts)
    ]
    assert not offenders, (
        "vendored README and CHANGELOG files are third-party artifacts, not "
        "instruction surfaces this repo authors, so npm install inside a skill "
        "must not turn the prose lints red: {offenders}".format(offenders=offenders)
    )


def test_the_prose_lints_inspect_a_real_corpus():
    surfaces = every_linted_markdown_file()
    assert len(surfaces) > 40, (
        "the prose lints found almost no instruction surfaces, so they would pass "
        "without inspecting anything"
    )
    longest = max(
        len(line)
        for path in surfaces
        for line in path.read_text().split("\n")
        if not line.lstrip().startswith(("#", "|"))
    )
    assert longest > 60, "the corpus has no prose lines long enough to exercise the cap"
