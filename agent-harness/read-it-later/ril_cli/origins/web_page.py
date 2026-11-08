from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from origins.transport import OriginTransport, bounded_text

LOGIN_WALLED_DOMAINS = (
    "instagram.com",
    "linkedin.com",
    "facebook.com",
    "tiktok.com",
    "threads.net",
    "threads.com",
)
SKIPPED_ELEMENTS = ("script", "style", "noscript", "svg", "template", "head")
MINIMUM_READABLE_CHARACTERS = 280
WHITESPACE = re.compile(r"\s+")


class ReadableTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skipped_depth = 0
        self.in_title = False
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attributes) -> None:
        self.skipped_depth += tag in SKIPPED_ELEMENTS
        self.in_title = self.in_title or tag == "title"

    def handle_endtag(self, tag: str) -> None:
        self.skipped_depth -= tag in SKIPPED_ELEMENTS and self.skipped_depth > 0
        self.in_title = self.in_title and tag != "title"

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
            return
        if self.skipped_depth == 0:
            self.text_parts.append(data)


def readable_text(html: str) -> tuple[str, str]:
    parser = ReadableTextParser()
    parser.feed(html)
    parser.close()
    title = WHITESPACE.sub(" ", " ".join(parser.title_parts)).strip()
    return title, WHITESPACE.sub(" ", " ".join(parser.text_parts)).strip()


def is_login_walled(url: str) -> bool:
    hostname = urlsplit(url).hostname or ""
    return any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in LOGIN_WALLED_DOMAINS
    )


def browser_needed(url: str, reason: str, effective_url: str = "") -> dict:
    return {
        "adapter": "web",
        "origin_id": url,
        "effective_url": effective_url or url,
        "title": "",
        "text": "",
        "needs_browser": True,
        "browser_reason": reason,
    }


def resolve_web_page(url: str, transport: OriginTransport) -> dict:
    if is_login_walled(url):
        return browser_needed(url, "login-walled site")
    page = transport.page(url)
    if page.content_type.startswith("image/"):
        return browser_needed(url, "image-only origin", page.effective_url)
    title, text = readable_text(page.body)
    if len(text) < MINIMUM_READABLE_CHARACTERS:
        return browser_needed(
            url,
            "too little readable text; likely rendered client side",
            page.effective_url,
        )
    return {
        "adapter": "web",
        "origin_id": url,
        "effective_url": page.effective_url,
        "title": title,
        "text": bounded_text(text),
        "needs_browser": False,
        "browser_reason": "",
    }
