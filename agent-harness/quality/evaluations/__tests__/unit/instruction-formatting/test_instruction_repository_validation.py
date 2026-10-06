from instructions.ai_instruction_format import inspect_markdown_instruction
from instructions.validation.instruction_repository_validation import (
    validate_instruction_sources,
)


def test_linked_target_added_during_validation_does_not_expand_source_workset(
    tmp_path,
):
    source = tmp_path / "source.md"
    target = tmp_path / "linked.md"
    metadata_fragment = tmp_path / "metadata.md"
    source.write_text("### Source\n\nRead [linked](linked.md#target).\n")
    target.write_text("# Target\n\n[Missing](missing.md)\n")
    metadata_fragment.write_text("")
    inspections = {source: inspect_markdown_instruction(source.read_text())}
    violations = []

    validate_instruction_sources(
        inspections,
        metadata_fragment,
        lambda path, violation: violations.append((path, violation)),
    )

    assert set(inspections) == {source, target}
    assert violations == []
