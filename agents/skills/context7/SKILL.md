---
name: context7
description: Fetch up-to-date library documentation from Context7. Use when user needs current docs for libraries, frameworks, or APIs that may have changed since training cutoff.
---

<usage>
Args format: `library query` where library is the name to search and query describes what docs to fetch.
Examples: `/context7 react hooks`, `/context7 next.js middleware authentication`, `/context7 prisma relations`
</usage>

<workflow>
1. Parse args: first word is library name, rest is query (defaults to "getting started" if no query)
2. Search for library ID via Context7 API
3. Fetch documentation using library ID and query
4. Present docs in text format ready for consumption
</workflow>

<api>
Base URL: https://context7.com
Search: GET /api/v2/libs/search?libraryName=X&query=Y - returns JSON with library matches
Docs: GET /api/v2/context?libraryId=X&query=Y&type=txt - returns documentation text
Auth: Bearer token header (optional). Set CONTEXT7_API_KEY env var for higher rate limits (keys have ctx7sk prefix).
</api>

<implementation>
Search for library:
```bash
curl -s "https://context7.com/api/v2/libs/search?libraryName=${library}&query=${query}" \
  ${CONTEXT7_API_KEY:+-H "Authorization: Bearer $CONTEXT7_API_KEY"} | jq -r '.results[0].libraryId'
```

Fetch docs with library ID:
```bash
curl -s "https://context7.com/api/v2/context?libraryId=${library_id}&query=${query}&type=txt" \
  ${CONTEXT7_API_KEY:+-H "Authorization: Bearer $CONTEXT7_API_KEY"}
```
</implementation>

<error_handling>
No library found: Inform user and suggest checking library name spelling or trying alternative names.
Empty docs: Library exists but query found no relevant content. Suggest broader query terms.
Rate limited: Suggest setting CONTEXT7_API_KEY env var for higher limits.
Network error: Report failure and suggest retrying.
</error_handling>

<output>
Present fetched documentation directly. No summarization unless user requests it. Include library name and query context at top. Docs are already formatted for LLM consumption.
</output>
