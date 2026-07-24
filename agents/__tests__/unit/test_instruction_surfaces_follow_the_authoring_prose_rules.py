from instruction_surface_prose import (
    MAXIMUM_INSTRUCTION_LINE_LENGTH,
    over_length_lines,
    prose_em_dash_lines,
)
from instruction_surface_scanner import REPO_ROOT, every_linted_markdown_file


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


def test_no_instruction_surface_uses_an_em_dash_in_its_own_prose():
    offenders = {
        str(path.relative_to(REPO_ROOT)): prose_em_dash_lines(path)[:3]
        for path in every_linted_markdown_file()
        if prose_em_dash_lines(path)
    }
    assert not offenders, (
        "an em dash in instruction prose contradicts the punctuation rule these "
        "surfaces themselves impose; recast with a colon, a semicolon, or a comma. "
        "Em dashes inside code fences, inline code, and quoted literals are exempt "
        f"because they are emitted artifacts, not prose: {offenders}"
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
