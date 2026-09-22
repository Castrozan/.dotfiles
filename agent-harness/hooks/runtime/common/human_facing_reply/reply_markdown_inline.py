class ReplyInlineContent:
    def __init__(self, children):
        visible = []
        outside_code = []
        self.destinations = []
        for child in children:
            if child.type == "link_open":
                self.destinations.append(child.attrGet("href"))
            if child.type in ("softbreak", "hardbreak"):
                visible.append("\n")
                outside_code.append("\n")
            elif child.type in ("text", "code_inline"):
                visible.append(child.content)
                outside_code.append(child.content if child.type == "text" else " ")
        self.visible_text = "".join(visible)
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


class ReplyLabelLine:
    def __init__(self, name, line_index, source_lines, parser):
        self.label = name
        self.line_index = line_index
        self.preceded_by_blank_line = (
            line_index == 0 or not source_lines[line_index - 1].strip()
        )
        children = parser.parseInline(source_lines[line_index])[0].children or []
        self.is_emphasized = label_is_emphasized(children, name)


def extract_reply_labels(source_lines, eligible_lines, configuration, parser):
    labels = []
    for index in sorted(eligible_lines):
        for name, pattern in configuration.label_patterns.items():
            if pattern.match(source_lines[index]):
                labels.append(ReplyLabelLine(name, index, source_lines, parser))
                break
    return labels
