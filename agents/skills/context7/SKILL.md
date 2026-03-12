---
name: context7
description: Fetch up-to-date library documentation from Context7. Use when user needs current docs for libraries, frameworks, or APIs that may have changed since training cutoff.
---

<usage>
Args format: `library query` where library is the name to search and query describes what docs to fetch. Defaults to "getting started" if no query provided.
</usage>

<workflow>
Search for library ID via Context7 API, then fetch documentation using that ID and the query. Present docs directly without summarization unless requested. Set CONTEXT7_API_KEY env var for higher rate limits.
</workflow>

<error_handling>
No library found: suggest checking spelling or trying alternative names. Empty docs: library exists but query found no relevant content, suggest broader terms. Rate limited: suggest setting CONTEXT7_API_KEY.
</error_handling>
