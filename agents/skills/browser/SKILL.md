---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

<architecture>
Pinchtab runs Chrome behind an HTTP API at `http://localhost:9867`. Two modes: headless (default, no window) and headed (user sees the browser). Use headed for login flows, CAPTCHAs, verification codes, or when user asks to see the browser. Cookies persist in `~/.pinchtab/chrome-profile/` across restarts and mode switches.
</architecture>

<startup>
Run `pinchtab-ensure-running` with `run_in_background: true` and `timeout: 120000` for headless. Run `pinchtab-switch-mode headed` with `run_in_background: true` for headed mode. Both are idempotent. Health-check separately after startup:

```bash
sleep 4 && curl -sf --max-time 3 http://localhost:9867/health
```

After user logs in via headed mode, switch back to headless — the session carries over.

The Bash tool sandbox sends SIGUSR2 to background processes, producing exit code 144. This is expected — not an error. Only trust the health endpoint for status. Run each pinchtab step as a separate Bash call — never chain with `&&` or `;`, as exit 144 from one command aborts the chain.
</startup>

<interaction-pattern>
Every browser interaction is one tool call. Helper scripts combine navigate/action + wait-for-stabilization + snapshot.

**Navigate and observe** — returns interactive snapshot listing all clickable/fillable elements:
```bash
pinchtab-navigate-and-snapshot "https://example.com"
```
Output:
```
# Example Domain | https://example.com/ | 1 nodes
e0:link "Learn more"
```

**Act and observe** — executes action, returns only what changed (~500 tokens):
```bash
pinchtab-act-and-snapshot '{"kind":"click","ref":"e0"}'
```
Output:
```json
{"added":null,"changed":null,"counts":{"added":0,"changed":0,"removed":0,"total":117},"diff":true,"removed":null,"title":"Example Domains","url":"https://www.iana.org/help/example-domains"}
```

**Screenshot** — captures image, then Read the file:
```bash
pinchtab-screenshot /tmp/screenshot.jpg
```

**Read page text** (~800 tokens, no element refs):
```bash
curl -s http://localhost:9867/text | python3 -c "import sys,json; print(json.load(sys.stdin).get('text',''))"
```

**Evaluate JavaScript** (synchronous only — async/promises return `{}`):
```bash
curl -s -X POST http://localhost:9867/evaluate -H "Content-Type: application/json" -d '{"expression":"document.title"}'
```

**Re-snapshot with interactive filter** (when you need to find new elements after an action):
```bash
pinchtab-act-and-snapshot '{"kind":"click","ref":"e5"}' "filter=interactive&format=compact"
```

Fall back to raw curl only when you need fine-grained control that helpers don't cover.
</interaction-pattern>

<snapshot-output-format>
Snapshots list interactive elements with refs you use in actions:
```
# Page Title | https://url | N nodes
e0:link "Link text"
e1:button "Button label"
e2:textbox "Placeholder"
e3:combobox "Search"
e4:checkbox "Remember me"
```

The `eN` ref is what you pass as `"ref"` in action payloads. Element types match ARIA roles: link, button, textbox, combobox, checkbox, menuitem, searchbox, etc.
</snapshot-output-format>

<actions>
Action JSON payloads for `pinchtab-act-and-snapshot`:
```json
{"kind":"click","ref":"e5"}
{"kind":"fill","ref":"e3","text":"hello"}
{"kind":"type","ref":"e3","text":"hello"}
{"kind":"press","key":"Enter"}
{"kind":"hover","ref":"e5"}
{"kind":"select","ref":"e7","values":["option1"]}
{"kind":"scroll","direction":"down","amount":500}
{"kind":"focus","ref":"e3"}
```

`fill` replaces input content. `type` appends characters. Snapshot query params: `filter=interactive`, `selector=CSS`, `diff=true`, `depth=N`, `format=compact`.
</actions>

<observation-strategy>
Choose the cheapest observation that answers your question:

| Method | Tokens | When to use |
|--------|--------|-------------|
| `diff=true&format=compact` | ~500 | After actions — see what changed (default for act-and-snapshot) |
| `/text` endpoint | ~800 | Reading page content, verifying text appeared |
| Screenshot + Read | ~1,500 | Visual verification, layout issues, images |
| `filter=interactive&format=compact` | ~3,600 | Find clickable elements (default for navigate-and-snapshot) |
| Full `/snapshot` | ~10,000 | Complete DOM structure — rarely needed |

Default flow: navigate with interactive filter to discover elements → act with diff to see changes → escalate to interactive filter again only when diff shows new elements appeared. Use `/text` when verifying content. Screenshot only for visual confirmation.
</observation-strategy>

<react-and-framework-forms>
React, Ant Design, and MUI components intercept native DOM events. Standard `fill` and `click` actions silently fail — the value appears set but framework state doesn't update, so submitting sends stale data.

**Detection**: look for class names `ant-select`, `ant-input`, `ant-picker`, `MuiInput`, `MuiSelect`, `rc-select`, or `data-reactroot` attributes in the snapshot or page source.

**Solution**: use `pinchtab-fill-react-form` which takes CSS selectors (not `eN` refs):
```bash
pinchtab-fill-react-form '[
  {"selector":"#email","value":"user@example.com"},
  {"selector":"#password","value":"secret123"},
  {"selector":".ant-select","value":"Administrator","type":"select"}
]'
```
Output:
```json
[{"selector":"#email","success":true,"type":"text"},{"selector":"#password","success":true,"type":"text"},{"selector":".ant-select","success":true,"type":"select","value":"Administrator"}]
```

Field types: `text` (default) uses React's native value setter + synthetic input/change events. `select` opens the Ant Design dropdown via mousedown and clicks the matching option by text.

**Important**: `pinchtab-fill-react-form` uses **CSS selectors** (like `#id`, `.class`, `input[name="x"]`), not snapshot `eN` refs. To find the right selector, use evaluate: `curl -s -X POST http://localhost:9867/evaluate -H "Content-Type: application/json" -d '{"expression":"document.querySelector(\"input\")?.id"}'`

Never retry `fill`/`click` on React components. If the first attempt doesn't stick, switch to `pinchtab-fill-react-form` or direct evaluate immediately.
</react-and-framework-forms>

<token-budgeting>
Plan interaction sequences before executing. Batch form fills with `pinchtab-fill-react-form` instead of one-field-at-a-time. After clicking, use diff — don't re-snapshot the entire page. Skip observation entirely for predictable outcomes (closing modals, pressing Enter). For 3+ actions with known outcomes, chain acts then observe once at the end. Use `/text` endpoint instead of snapshot when verifying content appeared.
</token-budgeting>

<complex-automation>
For sequences exceeding 10 browser actions, write a dedicated JavaScript script using the CDP pattern from `agents/skills/ponto/scripts/cdp-browser.js`. Connect directly to Chrome's WebSocket debug port, execute all DOM interactions in a single Node.js script, return structured results. Use for multi-step wizards, paginated scraping, complex login flows, or any automation that would otherwise burn excessive tool calls.
</complex-automation>

<workflow-example>
Complete example: navigate to a site, search, click a result.

```bash
# 1. Ensure pinchtab is running (separate call, run_in_background: true)
pinchtab-ensure-running

# 2. Health check (separate call)
sleep 4 && curl -sf --max-time 3 http://localhost:9867/health

# 3. Navigate — get interactive elements
pinchtab-navigate-and-snapshot "https://en.wikipedia.org"
# Output: e3:button "Search" ...

# 4. Click search
pinchtab-act-and-snapshot '{"kind":"click","ref":"e3"}'
# Output: diff showing search page loaded, new elements

# 5. Re-snapshot to find the search input ref
pinchtab-act-and-snapshot '{"kind":"click","ref":"e3"}' "filter=interactive&format=compact"
# Output: e16:searchbox "Search Wikipedia" ...

# 6. Fill search box and submit
pinchtab-act-and-snapshot '{"kind":"fill","ref":"e16","text":"Nix package manager"}'
pinchtab-act-and-snapshot '{"kind":"press","key":"Enter"}' "filter=interactive&format=compact"
# Output: search results with clickable links

# 7. Read text content instead of full snapshot
curl -s http://localhost:9867/text | python3 -c "import sys,json; print(json.load(sys.stdin).get('text',''))"
```

Each numbered step is ONE Bash tool call. Total: 7 calls for a full search workflow.
</workflow-example>

<troubleshooting>
Pinchtab won't start: graceful shutdown (`curl -sf --max-time 2 -X POST http://localhost:9867/shutdown`), clear locks (`rm -f ~/.pinchtab/chrome-profile/Singleton*`), check `/tmp/pinchtab.log`. Last resort only: `pkill -f pinchtab`.

Bot detection or CAPTCHA: set `BRIDGE_STEALTH=full` env var on startup for full canvas/WebGL spoofing.

Tab API supports new and close only — no tab switching. Navigate within the active tab.
</troubleshooting>
