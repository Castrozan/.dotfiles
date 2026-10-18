import json
import threading
import time
import uuid
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from agent_api.contract import CapabilityError, OperationRequest
from agent_api.service import CapabilityService


@pytest.fixture
def website():
    requests = Counter()
    routes = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests[self.path] += 1
            status, headers, body = routes.get(self.path, (404, {}, b"missing"))
            if self.path == "/slow":
                time.sleep(3)
            self.send_response(status)
            for name, value in headers.items():
                self.send_header(name, value)
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *arguments):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    routes["/robots.txt"] = (
        200,
        {"content-type": "text/plain"},
        b"User-agent: *\nDisallow: /blocked\n",
    )
    yield origin, routes, requests
    server.shutdown()
    server.server_close()
    thread.join()


def html(body):
    return 200, {"content-type": "text/html"}, body.encode()


def run_crawl(tmp_path, origin, **parameters):
    service = CapabilityService(tmp_path / "state")
    identifier = str(uuid.uuid4())
    request = OperationRequest("web.crawl", {"url": origin + "/", **parameters}, 30)
    receipt = service.run(identifier, request)
    output = receipt["result"]["output"]
    pages = [
        json.loads(line)
        for line in (service.store.directory(identifier) / output["artifact"])
        .read_text()
        .splitlines()
    ]
    return service, identifier, request, receipt, output, pages


def test_crawl_extracts_records_deduplicates_and_replays_without_network(
    tmp_path, website
):
    origin, routes, requests = website
    routes["/"] = html(
        "<title>Catalogue</title><article><h2>One</h2><p>Catalogue description: "
        "this fixture contains useful product information for extraction. "
        'Each product has a title and a link that can be reused by an agent.</p><a href="/item">item</a>'
        '</article><a href="/item#duplicate">duplicate</a>'
        '<a href="/blocked">blocked</a><a href="https://example.com/">outside</a>'
    )
    routes["/item"] = html("<title>Item</title><article><h2>Two</h2></article>")
    result = run_crawl(
        tmp_path,
        origin,
        extraction={
            "item_selector": "article",
            "fields": {"title": "h2::text", "link": "a::attr(href)"},
        },
    )
    service, identifier, request, receipt, output, pages = result
    assert len(pages) == 2
    assert pages[0]["records"] == [{"title": "One", "link": "/item"}]
    assert pages[1]["records"] == [{"title": "Two", "link": None}]
    assert "Catalogue description" in pages[0]["markdown"]
    assert output["javascript_rendered"] is False
    assert requests["/item"] == 1
    assert requests["/blocked"] == 0
    assert any(error["error"] == "robots_denied" for error in output["errors"])
    assert receipt["result"]["charge_usd"] == 0
    before = requests.copy()
    assert service.run(identifier, request) == receipt
    assert requests == before


@pytest.mark.parametrize(
    "limits, expected", [({"max_pages": 2}, 2), ({"max_depth": 0}, 1)]
)
def test_page_and_depth_limits_bound_actual_requests(
    tmp_path, website, limits, expected
):
    origin, routes, requests = website
    routes["/"] = html("".join(f'<a href="/{index}">page</a>' for index in range(20)))
    for index in range(20):
        routes[f"/{index}"] = html('<p>page content</p><a href="/deep">deeper</a>')
    *_, output, pages = run_crawl(tmp_path, origin, **limits)
    assert len(pages) == expected
    assert (
        sum(count for path, count in requests.items() if path != "/robots.txt")
        == expected
    )
    assert output["scheduled_pages"] == expected


def test_external_redirect_binary_oversize_and_failure_are_reported_without_retry(
    tmp_path, website
):
    origin, routes, requests = website
    routes["/"] = html(
        '<a href="/redirect">redirect</a><a href="/binary">binary</a>'
        '<a href="/large">large</a><a href="/error">error</a>'
    )
    routes["/redirect"] = (
        302,
        {"location": origin.replace("127.0.0.1", "localhost") + "/never"},
        b"",
    )
    routes["/binary"] = (200, {"content-type": "application/octet-stream"}, b"data")
    routes["/large"] = (200, {"content-type": "text/html"}, b"x" * (1024 * 1024 + 1))
    routes["/error"] = (503, {}, b"unavailable")
    *_, output, pages = run_crawl(tmp_path, origin)
    assert len(pages) == 1
    assert len(output["errors"]) == 4
    assert "outside_origin" in {error["error"] for error in output["errors"]}
    assert "unsupported_content_type" in {error["error"] for error in output["errors"]}
    assert requests["/error"] == 1
    assert requests["/never"] == 0


def test_crawl_deadline_stops_worker_and_marks_receipt_failed(tmp_path, website):
    origin, routes, requests = website
    routes["/slow"] = html("<p>slow</p>")
    service = CapabilityService(tmp_path / "state")
    identifier = str(uuid.uuid4())
    request = OperationRequest("web.crawl", {"url": origin + "/slow"}, 1)
    with pytest.raises(CapabilityError, match="deadline_exceeded"):
        service.run(identifier, request)
    assert service.store.inspect(identifier)["status"] == "failed"
    assert requests["/slow"] <= 1


def test_crawl_with_no_successful_pages_fails_instead_of_returning_empty_success(
    tmp_path, website
):
    origin, routes, requests = website
    service = CapabilityService(tmp_path / "state")
    identifier = str(uuid.uuid4())
    request = OperationRequest("web.crawl", {"url": origin + "/blocked"}, 30)
    with pytest.raises(CapabilityError, match="crawl_empty"):
        service.run(identifier, request)
    assert service.store.inspect(identifier)["status"] == "failed"
    assert requests["/blocked"] == 0
