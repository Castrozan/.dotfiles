---
name: sourcebot
description: Search code across GitLab repositories using Sourcebot. Use when searching for code patterns, functions, classes, APIs, or files across work repositories at gitlab.services.betha.cloud, or when managing the Sourcebot service.
---

<search>
POST http://localhost:3000/api/search with JSON body:

```bash
curl -s -X POST http://localhost:3000/api/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"<pattern>","matches":<count>}'
```

Query syntax:
- Keywords: `foo bar` (AND), `"exact phrase"`
- Regex: `foo.*bar`, `function\s+\w+`
- Filters: `repo:<name>` `lang:<language>` `file:<path>` `rev:<branch>` `sym:<symbol>`
- Negate: `-lang:YAML` `-file:test`
- Boolean: `foo (bar or baz)`, spaces for AND, `or` for OR

Response `files[]` contains: `fileName`, `repository`, `webUrl`, `language`, `chunks[]` (matching code with `content` and `matchRanges`), `branches[]`.

Always set `matches` to a reasonable number (5-20). Increase only if needed.
</search>

<management>
CLI commands:
- `sourcebot status` — check if running
- `sourcebot start` — start container and open browser
- `sourcebot stop` — stop container
- `sourcebot logs` — follow container logs
- `sourcebot update` — pull latest image
- `sourcebot rm` — remove container (keeps data)

Data: ~/.local/share/sourcebot/
Config: ~/.local/share/sourcebot/config.json
</management>

<workflow>
1. Before searching, verify Sourcebot is running: `sourcebot status`
2. If not running, start it: `sourcebot start`
3. Search using the API — parse results and use `webUrl` to link to GitLab source
4. Refine searches with filters when results are too broad
</workflow>
