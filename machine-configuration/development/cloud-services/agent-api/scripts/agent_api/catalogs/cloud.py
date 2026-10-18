from agent_api.catalogs.local import capability, text


def cloud_capabilities():
    identifier = text(256)
    identifier["pattern"] = r"^[A-Za-z0-9][A-Za-z0-9._/-]*$"
    provider = text(100)
    provider["pattern"] = r"^[a-z0-9][a-z0-9-]*$"
    return [
        capability(
            "monid.discover",
            "monid",
            "Search Monid's live provider catalog; discovery does not execute tools.",
            {
                "query": text(1000),
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            ["query"],
        ),
        capability(
            "monid.inspect",
            "monid",
            "Read a Monid endpoint's input schema, documentation and pricing.",
            {"provider": provider, "endpoint": text(256)},
            ["provider", "endpoint"],
        ),
        capability(
            "monid.run",
            "monid",
            "Execute one discovered Monid endpoint and await its result; requires explicit payment permission.",
            {"provider": provider, "endpoint": text(256), "input": {"type": "object"}},
            ["provider", "endpoint", "input"],
            "provider_plan",
        ),
        capability(
            "monid.result",
            "monid",
            "Retrieve an existing Monid run without resubmitting it.",
            {"run_id": identifier},
            ["run_id"],
        ),
        capability(
            "fal.run",
            "fal",
            "Run a fal image, video, audio or 3D model through its durable queue using the model's documented input.",
            {"endpoint": identifier, "input": {"type": "object"}},
            ["endpoint", "input"],
            "provider_plan",
        ),
        capability(
            "fal.result",
            "fal",
            "Read an existing fal request using its retained status and response URLs; never resubmits.",
            {"status_url": text(), "response_url": text()},
            ["status_url", "response_url"],
        ),
        capability(
            "web.search",
            "firecrawl",
            "Search the web through Firecrawl's limited unauthenticated access or your account.",
            {
                "query": text(1000),
                "limit": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            ["query"],
            "optional_account",
        ),
        capability(
            "web.scrape",
            "firecrawl",
            "Extract rendered page Markdown through Firecrawl; public access is rate limited.",
            {"url": text()},
            ["url"],
            "optional_account",
        ),
    ]
