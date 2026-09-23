import re


class ReplyInlineContent:
    def __init__(self, children):
        outside_code = []
        self.destinations = []
        for child in children:
            if child.type == "link_open":
                self.destinations.append(child.attrGet("href"))
            if child.type in ("softbreak", "hardbreak"):
                outside_code.append("\n")
            elif child.type in ("text", "code_inline"):
                outside_code.append(child.content if child.type == "text" else " ")
        self.outside_code = "".join(outside_code)


def label_is_emphasized(children, name):
    meaningful = [
        child for child in children if child.type != "text" or child.content.strip()
    ]
    if not meaningful or meaningful[0].type != "strong_open":
        return False
    emphasized = []
    for child in meaningful[1:]:
        if child.type == "strong_close":
            break
        if child.type == "text":
            emphasized.append(child.content)
    text = "".join(emphasized).casefold()
    return text == name.casefold() or text.startswith(name.casefold() + ":")


def label_has_inline_content(children, label_pattern):
    text = []
    for child in children:
        if child.type in ("softbreak", "hardbreak") or (
            child.type == "html_inline"
            and re.match(r"<br(?:\s|/?>)", child.content, re.IGNORECASE)
        ):
            break
        if child.type == "image":
            return True
        if child.type in ("text", "code_inline"):
            text.append(child.content)
    rendered_text = "".join(text)
    match = label_pattern.match(rendered_text)
    return bool(match and rendered_text[match.end() :].strip())


class ReplyLabelLine:
    def __init__(self, name, line_index, source_lines, parser, label_pattern):
        self.label = name
        self.line_index = line_index
        self.preceded_by_blank_line = (
            line_index == 0 or not source_lines[line_index - 1].strip()
        )
        children = parser.parseInline(source_lines[line_index] + "\n")[0].children or []
        self.is_emphasized = label_is_emphasized(children, name)
        self.has_inline_content = label_has_inline_content(children, label_pattern)


def extract_reply_labels(source_lines, eligible_lines, configuration, parser):
    labels = []
    for index in sorted(eligible_lines):
        for name, pattern in configuration.label_patterns.items():
            if pattern.match(source_lines[index]):
                labels.append(
                    ReplyLabelLine(name, index, source_lines, parser, pattern)
                )
                break
    return labels
