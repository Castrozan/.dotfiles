from pathlib import PurePosixPath

import pytest

from instructions.instruction_link_rebasing import rebase_instruction_links

SOURCE = PurePosixPath("/instructions/skills/read/SKILL.md")
DEPLOYED = PurePosixPath("/home/example/.codex/skills/read/SKILL.md")
DESTINATIONS = {
    SOURCE.parent: DEPLOYED.parent,
    PurePosixPath("/instructions/core-rules/core.md"): DEPLOYED.parent.parent
    / "core/SKILL.md",
}


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "Read [core](../../core-rules/core.md#evidence).",
            "Read [core](../core/SKILL.md#evidence).",
        ),
        ("Read [here](#evidence).", "Read [here](#evidence)."),
        (
            "Read [source](references/source.md#evidence).",
            "Read [source](references/source.md#evidence).",
        ),
        (
            "Read [docs](https://example.com/#evidence).",
            "Read [docs](https://example.com/#evidence).",
        ),
        (
            'Read [core](<../../core-rules/core.md#evidence> "Title").',
            'Read [core](<../core/SKILL.md#evidence> "Title").',
        ),
        (
            'Read [docs](<https://example.com/#evidence> "Title").',
            'Read [docs](<https://example.com/#evidence> "Title").',
        ),
        (
            "Read `[literal](../../core-rules/core.md#evidence)` and [core](../../core-rules/core.md#evidence).",
            "Read `[literal](../../core-rules/core.md#evidence)` and [core](../core/SKILL.md#evidence).",
        ),
        (
            "Read [core]\n(../../core-rules/core.md#evidence).",
            "Read [core]\n(../../core-rules/core.md#evidence).",
        ),
        (
            "Read [core](../../core-rules/core.md#evidence)\nand [again](../../core-rules/core.md#evidence).",
            "Read [core](../core/SKILL.md#evidence)\nand [again](../core/SKILL.md#evidence).",
        ),
    ],
)
def test_rebases_only_parsed_link_destinations_and_preserves_prose(source, expected):
    text = f"### Evidence\n\n{source}\n"
    assert (
        rebase_instruction_links(text, SOURCE, DEPLOYED, DESTINATIONS)
        == f"### Evidence\n\n{expected}\n"
    )


def test_preserves_frontmatter_and_links_inside_its_literals():
    metadata = '---\nname: example\ndescription: "[literal](../../core-rules/core.md)"\n---\n\n'
    text = (
        metadata + "### Evidence\n\nRead [core](../../core-rules/core.md#evidence).\n"
    )
    assert rebase_instruction_links(text, SOURCE, DEPLOYED, DESTINATIONS) == (
        metadata + "### Evidence\n\nRead [core](../core/SKILL.md#evidence).\n"
    )


def test_rejects_a_source_target_without_a_deployed_owner():
    text = "### Evidence\n\nRead [unshipped](../../unshipped.md#evidence).\n"
    with pytest.raises(ValueError, match="deployed destination"):
        rebase_instruction_links(text, SOURCE, DEPLOYED, DESTINATIONS)


def test_maps_concatenated_source_fragments_to_the_same_deployed_file():
    destinations = {
        **DESTINATIONS,
        PurePosixPath("/instructions/core-rules/core.md"): DEPLOYED,
    }
    text = "### Evidence\n\nRead [core](../../core-rules/core.md#coding).\n"
    assert rebase_instruction_links(text, SOURCE, DEPLOYED, destinations) == (
        "### Evidence\n\nRead [core](#coding).\n"
    )


def test_preserves_crlf_while_rebasing_a_link_after_frontmatter():
    source = "---\r\nname: example\r\n---\r\n\r\n### Evidence\r\n\r\nRead [core](../../core-rules/core.md#evidence).\r\n"
    expected = source.replace("../../core-rules/core.md", "../core/SKILL.md")
    assert rebase_instruction_links(source, SOURCE, DEPLOYED, DESTINATIONS) == expected
