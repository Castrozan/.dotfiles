import uuid

import pytest

from agent_api.catalog import describe, validate_request
from agent_api.contract import CapabilityError, OperationRequest
from agent_api.service import CapabilityService


@pytest.mark.parametrize(
    "parameters",
    [
        {"max_pages": 0},
        {"max_pages": 51},
        {"max_depth": -1},
        {"max_depth": 6},
        {"browser": True},
    ],
)
def test_crawl_rejects_unbounded_or_browser_controls(parameters):
    with pytest.raises(CapabilityError, match="invalid_input"):
        validate_request(
            OperationRequest("web.crawl", {"url": "https://example.com", **parameters})
        )


@pytest.mark.parametrize("item_selector", ["[", "article::text"])
def test_invalid_extraction_selector_fails_before_operation_claim(
    tmp_path, item_selector
):
    service = CapabilityService(tmp_path / "state")
    identifier = str(uuid.uuid4())
    request = OperationRequest(
        "web.crawl",
        {
            "url": "https://example.com",
            "extraction": {
                "item_selector": item_selector,
                "fields": {"title": "h1::text"},
            },
        },
    )
    with pytest.raises(CapabilityError, match="invalid_selector"):
        service.run(identifier, request)
    with pytest.raises(CapabilityError, match="operation_not_found"):
        service.store.inspect(identifier)


def test_crawl_contract_is_free_and_discoverable():
    entry = describe("web.crawl")
    assert entry["provider"] == "scrapy"
    assert entry["payment"] == "none"


@pytest.mark.parametrize(
    "body",
    ["<article>value</article>" * 1001, "<article>" + "x" * 16385 + "</article>"],
)
def test_structured_extraction_bounds_records_and_individual_fields(tmp_path, body):
    from scrapy.http import HtmlResponse

    from agent_api.providers.site_spider import SiteSpider

    spider = SiteSpider(
        {
            "url": "https://example.com",
            "extraction": {"item_selector": "article", "fields": {"value": "::text"}},
        },
        tmp_path,
    )
    response = HtmlResponse("https://example.com", body=body.encode(), encoding="utf-8")
    with pytest.raises(CapabilityError, match="extraction_too_large"):
        spider.records(response)
