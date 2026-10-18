from urllib.parse import urlsplit

from scrapy import Request, Spider
from scrapy.exceptions import IgnoreRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.spidermiddlewares.httperror import HttpError
from trafilatura import extract
from w3lib.url import canonicalize_url

from agent_api.contract import (
    MAXIMUM_RESULT_BYTES,
    CapabilityError,
    canonical_json,
    validate_url,
)


def origin(url):
    parsed = urlsplit(validate_url(url))
    return (
        parsed.scheme,
        parsed.hostname,
        parsed.port or (443 if parsed.scheme == "https" else 80),
    )


class OriginMiddleware:
    def process_request(self, request, spider):
        try:
            if origin(request.url) == spider.origin:
                return None
        except CapabilityError:
            pass
        raise IgnoreRequest("outside_origin")


class SiteSpider(Spider):
    name = "agent_api_site"

    def __init__(self, parameters, directory, **arguments):
        super().__init__(**arguments)
        self.start_url = canonicalize_url(parameters["url"])
        self.origin = origin(self.start_url)
        self.maximum_pages = parameters.get("max_pages", 10)
        self.maximum_depth = parameters.get("max_depth", 2)
        self.extraction = parameters.get("extraction")
        self.directory = directory
        self.scheduled_urls = {self.start_url}
        self.pages = []
        self.errors = []
        self.link_extractor = LinkExtractor(canonicalize=True)

    async def start(self):
        yield Request(
            self.start_url,
            callback=self.parse,
            errback=self.failed,
            meta={"crawl_depth": 0},
        )

    def parse(self, response):
        try:
            page = self.page(response)
        except CapabilityError as error:
            self.errors.append({"url": response.url, "error": str(error)})
            return
        with (self.directory / "crawl.jsonl").open("ab") as output:
            output.write(canonical_json(page) + b"\n")
        self.pages.append(
            {
                "url": page["url"],
                "depth": page["depth"],
                "title": page["title"],
                "record_count": len(page["records"]),
            }
        )
        yield from self.follow(response, page["depth"])

    def eligible(self, url):
        if url in self.scheduled_urls:
            return False
        try:
            return origin(url) == self.origin
        except CapabilityError:
            return False

    def follow(self, response, depth):
        if depth >= self.maximum_depth:
            return
        for link in self.link_extractor.extract_links(response):
            if len(self.scheduled_urls) >= self.maximum_pages:
                return
            if not self.eligible(link.url):
                continue
            self.scheduled_urls.add(link.url)
            yield Request(
                link.url,
                callback=self.parse,
                errback=self.failed,
                meta={"crawl_depth": depth + 1},
            )

    def page(self, response):
        content_type = (
            response.headers.get(b"Content-Type", b"").split(b";")[0].strip().lower()
        )
        if content_type not in (b"text/html", b"application/xhtml+xml", b"text/plain"):
            raise CapabilityError("unsupported_content_type")
        page = {
            "url": response.url,
            "depth": response.meta["crawl_depth"],
            "title": (response.css("title::text").get() or "")[:512],
            "markdown": self.markdown(response, content_type),
            "records": self.records(response),
        }
        if len(canonical_json(page)) > MAXIMUM_RESULT_BYTES:
            raise CapabilityError("response_too_large")
        return page

    def markdown(self, response, content_type):
        if content_type == b"text/plain":
            return response.text
        return (
            extract(
                response.body,
                url=response.url,
                output_format="markdown",
                include_links=True,
                include_tables=True,
                include_comments=False,
            )
            or ""
        )

    def records(self, response):
        if self.extraction is None:
            return []
        items = response.css(self.extraction["item_selector"])
        if len(items) > 1000:
            raise CapabilityError("extraction_too_large")
        records = []
        size = 0
        for item in items:
            record = self.record(item)
            size += len(canonical_json(record))
            if size > MAXIMUM_RESULT_BYTES:
                raise CapabilityError("extraction_too_large")
            records.append(record)
        return records

    def record(self, item):
        record = {}
        for name, expression in self.extraction["fields"].items():
            value = item.css(expression).get()
            if value is not None and len(value) > 16 * 1024:
                raise CapabilityError("extraction_too_large")
            record[name] = value
        return record

    def failed(self, failure):
        error = "fetch_failed"
        if failure.check(HttpError):
            error = "http_error"
        elif failure.check(IgnoreRequest):
            if "robots.txt" in str(failure.value):
                error = "robots_denied"
            elif str(failure.value) == "outside_origin":
                error = "outside_origin"
            else:
                error = "request_denied"
        self.errors.append({"url": failure.request.url, "error": error})
