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


def formatted_link_violation(reply):
    quote_depth = 0
    for token in reply.document.tokens:
        quote_depth += (token.type == "blockquote_open") - (
            token.type == "blockquote_close"
        )
        if quote_depth:
            continue
        if (token.type == "html_block" and html_has_formatted_links(token.content)) or (
            token.type == "inline" and inline_has_formatted_links(token.children or [])
        ):
            return reply.configuration.violation("formatted_link")
    return None
