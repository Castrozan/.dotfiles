from agent_api.catalogs.local import capability, object_schema, text


def cloud_capabilities():
    return [
        capability(
            "web.search",
            "firecrawl",
            "Search the web through Firecrawl's limited anonymous access.",
            object_schema(
                {
                    "query": text(1000),
                    "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                ["query"],
            ),
        ),
        capability(
            "web.scrape",
            "firecrawl",
            "Extract rendered page Markdown through Firecrawl's limited anonymous access.",
            object_schema({"url": text()}, ["url"]),
        ),
    ]
