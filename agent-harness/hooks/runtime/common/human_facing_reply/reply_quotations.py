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
        if character in ("'", "’") and is_apostrophe(text, index):
            continue
        if closing_character is not None:
            if character == closing_character:
                segments.append(text[retained_start:quotation_start])
                segments.append(" ")
                retained_start = index + 1
                closing_character = None
            continue
        if character in quotation_pairs:
            quotation_start = index
            closing_character = quotation_pairs[character]
    segments.append(text[retained_start:])
    return "".join(segments)
