import re
from html.parser import HTMLParser


class ReplyHtmlLinkDetector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.has_link = False

    def handle_starttag(self, tag, attributes):
        if tag in ("a", "area") and any(name == "href" for name, _ in attributes):
            self.has_link = True


def html_has_formatted_links(text):
    if "\x1b]8;" in text:
        return True
    detector = ReplyHtmlLinkDetector()
    detector.feed(text)
    return detector.has_link


def inline_has_formatted_links(children):
    return any(
        child.type == "link_open"
        or (child.type == "html_inline" and html_has_formatted_links(child.content))
        or (child.type == "text" and "\x1b]8;" in child.content)
        for child in children
    )


class ReplyInlineContent:
    def __init__(self, children):
        outside_code = []
        self.destinations = []
        self.has_formatted_links = inline_has_formatted_links(children)
        for child in children:
            if child.type == "link_open":
                self.destinations.append(child.attrGet("href"))
            if child.type in ("softbreak", "hardbreak"):
                outside_code.append("\n")
            elif child.type in ("text", "code_inline"):
                outside_code.append(child.content if child.type == "text" else " ")
        self.outside_code = "".join(outside_code)


def label_is_emphasized(children, name):
    meaningful = _meaningful_label_children(children)
    if not meaningful or meaningful[0].type != "strong_open":
        return False
    text = _emphasized_label_text(meaningful[1:]).casefold()
    return text == name.casefold() or text.startswith(name.casefold() + ":")


def _meaningful_label_children(children):
    return [
        child for child in children if child.type != "text" or child.content.strip()
    ]


def _emphasized_label_text(children):
    emphasized = []
    for child in children:
        if child.type == "strong_close":
            break
        if child.type == "text":
            emphasized.append(child.content)
    return "".join(emphasized)


def label_has_inline_content(children, label_pattern):
    text = []
    for child in children:
        if _is_inline_label_break(child):
            break
        if child.type == "image":
            return True
        if child.type in ("text", "code_inline"):
            text.append(child.content)
    rendered_text = "".join(text)
    match = label_pattern.match(rendered_text)
    return _match_has_inline_text(match, rendered_text)


def _is_inline_label_break(child):
    return child.type in ("softbreak", "hardbreak") or (
        child.type == "html_inline"
        and re.match(r"<br(?:\s|/?>)", child.content, re.IGNORECASE)
    )


def _match_has_inline_text(match, rendered_text):
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
