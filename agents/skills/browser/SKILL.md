---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

# Browser Automation

Pinchtab provides headless Chrome via HTTP API at `localhost:9867`. Helper scripts in `bin/` handle startup and screenshots.

<startup>
Start pinchtab before any browser operations. The startup script is idempotent — safe to call repeatedly.

```bash
# MUST use run_in_background:true — Claude's shell sandbox kills foreground long-lived processes
pinchtab-ensure-running    # Bash tool with run_in_background: true, timeout: 120000
```

Then health-check in a separate call:

```bash
sleep 4 && curl -sf --max-time 3 http://localhost:9867/health
```

If `pinchtab-ensure-running` is not in PATH, use the full path at `~/.dotfiles/bin/pinchtab-ensure-running`.

To stop: `pkill -f pinchtab`
</startup>

<workflow>
Pattern: navigate, read or snapshot, then act.

```bash
# Navigate to a URL
curl -s -X POST http://localhost:9867/navigate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'

# Read page text (~800 tokens, cheapest option)
curl -s http://localhost:9867/text | python3 -c "import sys,json; print(json.load(sys.stdin).get('text',''))"

# Get interactive elements with refs for clicking/typing
curl -s "http://localhost:9867/snapshot?filter=interactive&format=compact"

# Click element by ref
curl -s -X POST http://localhost:9867/action \
  -H "Content-Type: application/json" \
  -d '{"kind":"click","ref":"e5"}'

# Type into input
curl -s -X POST http://localhost:9867/action \
  -H "Content-Type: application/json" \
  -d '{"kind":"fill","ref":"e3","text":"search query"}'

# Press a key
curl -s -X POST http://localhost:9867/action \
  -H "Content-Type: application/json" \
  -d '{"kind":"press","key":"Enter"}'

# Execute JavaScript
curl -s -X POST http://localhost:9867/evaluate \
  -H "Content-Type: application/json" \
  -d '{"expression":"document.title"}'
```
</workflow>

<screenshots>
The `/screenshot` endpoint returns base64 JSON, not raw image bytes. Use the helper script to decode and validate:

```bash
pinchtab-screenshot /tmp/screenshot.jpg
# Then use Read tool on /tmp/screenshot.jpg
```

If not in PATH, use `~/.dotfiles/bin/pinchtab-screenshot`.

Never read a screenshot file without validating it first. If the API returns an error and you read the JSON as an image, the conversation context is poisoned — every subsequent image read fails. The session becomes unrecoverable.
</screenshots>

<endpoints>
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server status |
| `GET` | `/tabs` | List open tabs |
| `GET` | `/text` | Readable page text (cheapest) |
| `GET` | `/snapshot` | Accessibility tree with element refs |
| `GET` | `/screenshot` | Base64 JSON screenshot (use helper script) |
| `POST` | `/navigate` | Go to URL: `{"url":"..."}` |
| `POST` | `/action` | Interact: click, fill, type, press, hover, select, scroll, focus |
| `POST` | `/evaluate` | Execute JavaScript: `{"expression":"..."}` |
| `POST` | `/tab` | Manage tabs: `{"action":"new","url":"..."}` or `{"action":"close","id":"..."}` |
</endpoints>

<snapshot-filters>
```bash
# Interactive elements only (~75% fewer tokens)
curl -s "http://localhost:9867/snapshot?filter=interactive&format=compact"

# Scoped to a CSS selector
curl -s "http://localhost:9867/snapshot?selector=main&format=compact"

# Only changes since last snapshot
curl -s "http://localhost:9867/snapshot?diff=true&format=compact"

# Limit tree depth
curl -s "http://localhost:9867/snapshot?depth=3&format=compact"
```
</snapshot-filters>

<actions>
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

Use `fill` to replace input content. Use `type` to append characters.
</actions>

<token-efficiency>
| Method | Typical Tokens | Use When |
|--------|---------------|----------|
| `/text` | ~800 | Reading content only |
| `?filter=interactive` | ~3,600 | Need to click/type |
| Full snapshot | ~10,000 | Need page structure |
| Screenshot | ~2,000 | Visual verification |

Always use `/text` first when you only need to read. Use `?filter=interactive` when you need to act.
</token-efficiency>

<tabs>
Tab API supports only `new` and `close`. There is no tab activation — navigate within the current active tab.

```bash
# Open new tab
curl -s -X POST http://localhost:9867/tab \
  -H "Content-Type: application/json" \
  -d '{"action":"new","url":"https://example.com"}'

# Close tab by ID
curl -s -X POST http://localhost:9867/tab \
  -H "Content-Type: application/json" \
  -d '{"action":"close","id":"TAB_ID"}'

# List tabs
curl -s http://localhost:9867/tabs
```

The startup script uses `BRIDGE_NO_RESTORE=true` to prevent old tabs from polluting the session.
</tabs>

<session-persistence>
Cookies and auth persist in `~/.pinchtab/chrome-profile/` across restarts. Log in once, stay logged in.

For manual login (user must run from their terminal with display access):

```bash
BRIDGE_HEADLESS=false pinchtab
```

Navigate to sites, log in via the visible Chrome window, then Ctrl+C. Cookies are saved.
</session-persistence>

<stealth>
Pinchtab patches `navigator.webdriver` and spoofs User-Agent by default (stealth=light). For aggressive bot detection:

```bash
BRIDGE_STEALTH=full pinchtab
```
</stealth>

<environment-variables>
| Variable | Default | Description |
|----------|---------|-------------|
| `BRIDGE_HEADLESS` | `true` | Run Chrome in headless mode |
| `BRIDGE_PORT` | `9867` | HTTP API port |
| `BRIDGE_STEALTH` | `light` | Stealth level: `light` or `full` |
| `BRIDGE_NO_RESTORE` | `false` | Skip restoring tabs from previous session |
| `BRIDGE_NO_ANIMATIONS` | — | Disable CSS animations |
| `BRIDGE_BLOCK_IMAGES` | — | Block image loading |
| `BRIDGE_BLOCK_MEDIA` | — | Block media loading |
| `BRIDGE_NAV_TIMEOUT` | — | Navigation timeout |
| `BRIDGE_TIMEOUT` | — | General timeout |
| `BRIDGE_TIMEZONE` | — | Override timezone |
| `BRIDGE_TOKEN` | — | Auth token for API access |
| `BRIDGE_CHROME_VERSION` | — | Spoof Chrome version |
</environment-variables>

<cdp-access>
Pinchtab launches Chrome with a random CDP (Chrome DevTools Protocol) port. To find it:

```bash
ss -tlnp | grep chromium | grep -o '127\.0\.0\.1:[0-9]*' | head -1
```

Verify with:

```bash
curl -s http://127.0.0.1:PORT/json/version
```

This provides direct CDP WebSocket access for advanced use cases (network interception, performance profiling).

The mcporter chrome-devtools MCP is currently broken — its `npx chrome-devtools-mcp@latest` command hangs on network fetch. Use direct CDP HTTP/WebSocket as a workaround.
</cdp-access>

<troubleshooting>
Pinchtab won't start:
1. Check if already running: `curl -s http://localhost:9867/health`
2. Kill stale processes: `pkill -f pinchtab`
3. Clear Chrome lock files: `rm -f ~/.pinchtab/chrome-profile/Singleton*`
4. Check logs at `/tmp/pinchtab.log`

Exit code 144 from Bash tool:
This is normal — Claude's shell sandbox sends SIGUSR1 to long-running processes. Pinchtab may still be running. Always health-check separately.

Screenshot returns JSON not image:
Use `pinchtab-screenshot` helper. The `/screenshot` endpoint returns `{"base64":"...","format":"jpeg"}`, not raw bytes.
</troubleshooting>

<boundaries>
Never work around browser tool failures by launching browser binaries directly, connecting to CDP ports manually, using xdotool, or writing custom websocket/HTTP scripts. Use pinchtab and the helper scripts. If pinchtab fails, diagnose the underlying issue (port conflict, stale process, missing binary).
</boundaries>
