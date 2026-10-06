def is_instruction_heading(opening):
    return opening.type == "heading_open" and opening.tag == "h3"


def is_instruction_paragraph(opening, section_line_number):
    return opening.type == "paragraph_open" and section_line_number > 0


def valid_instruction_block(opening, following, heading, paragraph):
    if not (heading or paragraph):
        return False
    if opening.level != 0:
        return False
    return _valid_instruction_block_tokens(following, heading)


def _valid_instruction_block_tokens(following, heading):
    if len(following) != 2 or following[0].type != "inline":
        return False
    if not following[0].content.strip():
        return False
    return following[1].type == ("heading_close" if heading else "paragraph_close")


def record_heading_transition(inspection, section_line_number, section_prose_lines):
    if section_line_number and not section_prose_lines:
        inspection.reject(
            "instruction_section_structure",
            section_line_number,
            "expected prose after heading",
        )


def report_unconsumed_instruction_lines(body, consumed_lines, inspection):
    for row, line in enumerate(body.text.splitlines()):
        if line.strip() and row not in consumed_lines:
            inspection.reject(
                "instruction_source_coverage",
                body.first_line_number + row,
                "expected a heading or prose paragraph",
            )


def report_empty_instruction_section(
    body, section_line_number, section_prose_lines, inspection
):
    if not section_line_number or not section_prose_lines:
        inspection.reject(
            "instruction_section_structure",
            section_line_number or body.first_line_number,
            "expected a ### heading followed by nonempty prose",
        )
