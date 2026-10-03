def is_apostrophe(text, index):
    return (
        index > 0
        and index + 1 < len(text)
        and text[index - 1].isalnum()
        and text[index + 1].isalnum()
    )


def text_outside_quotations(text, quotation_pairs):
    segments = []
    retained_start = 0
    quotation_start = None
    closing_character = None
    for index, character in enumerate(text):
        if _is_apostrophe_character(text, index, character):
            continue
        consumed, retained_start, closing_character = _consume_active_quotation(
            text,
            index,
            character,
            segments,
            retained_start,
            quotation_start,
            closing_character,
        )
        if consumed:
            continue
        if character in quotation_pairs:
            quotation_start = index
            closing_character = quotation_pairs[character]
    segments.append(text[retained_start:])
    return "".join(segments)


def _is_apostrophe_character(text, index, character):
    return character in ("'", "’") and is_apostrophe(text, index)


def _consume_active_quotation(
    text,
    index,
    character,
    segments,
    retained_start,
    quotation_start,
    closing_character,
):
    if closing_character is None:
        return False, retained_start, closing_character
    if character != closing_character:
        return True, retained_start, closing_character
    segments.append(text[retained_start:quotation_start])
    segments.append(" ")
    return True, index + 1, None
