---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

# Browser Automation

Two browser tools available. **Pinchtab is primary** — faster, cheaper, more reliable. Use pw as fallback only.

## Pinchtab (Primary — HTTP API)

Standalone Go binary. Plain HTTP API at `localhost:9867`. Any agent, any language, even curl.

### Starting the Server

Pinchtab runs as a background process. Start it before use:

```bash
pinchtab &    # Headless by default (Nix wrapper handles env vars)
sleep 3       # Wait for Chrome to initialize
curl -s http://localhost:9867/health   # Verify: {"status":"ok"}
```

To stop: `pkill -f pinchtab`

### Core Workflow

```bash
# Navigate
curl -s -X POST http://localhost:9867/navigate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'

# Read page content (~800 tokens for a typical page)
curl -s http://localhost:9867/text | jq -r '.text'

# Get interactive elements (buttons, links, inputs) with refs
curl -s "http://localhost:9867/snapshot?filter=interactive&format=compact"

# Click element by ref
curl -s -X POST http://localhost:9867/action \
  -H "Content-Type: application/json" \
  -d '{"kind":"click","ref":"e5"}'

# Type into input
curl -s -X POST http://localhost:9867/action \
  -H "Content-Type: application/json" \
  -d '{"kind":"type","ref":"e3","text":"search query"}'

# List open tabs
curl -s http://localhost:9867/tabs

# Screenshot
curl -s "http://localhost:9867/screenshot" > /tmp/screenshot.jpg
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server status |
| `GET` | `/tabs` | List open tabs |
| `GET` | `/text` | Readable page text (cheapest — ~800 tokens) |
| `GET` | `/snapshot` | Accessibility tree with refs |
| `GET` | `/screenshot` | JPEG screenshot |
| `POST` | `/navigate` | Go to URL: `{"url":"..."}` |
| `POST` | `/action` | Interact: click, type, fill, press, hover, select, scroll |
| `POST` | `/evaluate` | Execute JavaScript |
| `POST` | `/tab` | Open/close tabs |

### Snapshot Filters (save tokens)

```bash
# Interactive elements only — buttons, links, inputs (~75% fewer tokens)
curl -s "http://localhost:9867/snapshot?filter=interactive&format=compact"

# Scoped to a section
curl -s "http://localhost:9867/snapshot?selector=main&format=compact"

# Only changes since last snapshot
curl -s "http://localhost:9867/snapshot?diff=true&format=compact"

# Limit tree depth
curl -s "http://localhost:9867/snapshot?depth=3&format=compact"
```

### Action Types

```json
{"kind":"click","ref":"e5"}
{"kind":"type","ref":"e3","text":"hello"}
{"kind":"fill","ref":"e3","text":"hello"}
{"kind":"press","key":"Enter"}
{"kind":"hover","ref":"e5"}
{"kind":"select","ref":"e7","values":["option1"]}
{"kind":"scroll","direction":"down","amount":500}
{"kind":"focus","ref":"e3"}
```

### Token Efficiency

| Method | Typical Tokens | Use When |
|--------|---------------|----------|
| `/text` | ~800 | Reading content only |
| `?filter=interactive` | ~3,600 | Need to click/type |
| Full snapshot | ~10,000 | Need page structure |
| Screenshot | ~2,000 | Visual verification |

**Always use `/text` first** when you only need to read. Use `?filter=interactive` when you need to act. Full snapshot only when structure matters.

### Session Persistence

Cookies and auth persist in `~/.pinchtab/chrome-profile/` across restarts. Log in once (headed mode), stay logged in forever.

### One-Time Login (Manual — Headed Mode)

Headed mode requires display access. User must run from their terminal:

```bash
BRIDGE_HEADLESS=false pinchtab
# Then navigate to sites and log in via the visible Chrome window
# Ctrl+C when done — cookies are saved to ~/.pinchtab/chrome-profile/
```

Or programmatic login (headless):

```bash
# Navigate to login page
curl -s -X POST http://localhost:9867/navigate -d '{"url":"https://site.com/login"}'
# Fill credentials
curl -s -X POST http://localhost:9867/action -d '{"kind":"fill","ref":"e3","text":"user@email.com"}'
curl -s -X POST http://localhost:9867/action -d '{"kind":"fill","ref":"e5","text":"password"}'
curl -s -X POST http://localhost:9867/action -d '{"kind":"click","ref":"e7"}'
```

### Stealth Mode

Pinchtab patches `navigator.webdriver` and spoofs User-Agent by default. For aggressive bot detection:

```bash
BRIDGE_STEALTH=full pinchtab   # Canvas/WebGL/font spoofing
```

## pw CLI (Fallback)

Playwright-based browser with Node.js daemon. Persistent browser at `~/.local/share/pw-browser/`.

```bash
pw open https://example.com     # Navigate
pw text                         # Page text
pw elements                     # Interactive elements with [index]
pw click 3                      # Click by index
pw snap                         # Accessibility tree
pw screenshot                   # Save screenshot
pw close                        # Kill browser
```

### When to Use pw Instead of Pinchtab

- Pinchtab server isn't running and you need a quick one-off command
- You need Playwright-specific features (actionability checks, auto-waiting)
- Pinchtab is broken/unavailable

### pw Headed Mode (for manual login)

```bash
pw open https://site.com/login --headed   # Visible browser for user to log in
```

## Chrome DevTools MCP (Frontend Development)

For network monitoring, performance profiling, and device emulation — use `mcporter`:

```bash
mcporter list chrome-devtools              # List available tools
mcporter call chrome-devtools.navigate_page type=url url=https://example.com
mcporter call chrome-devtools.list_network_requests
mcporter call chrome-devtools.take_screenshot
```

## Troubleshooting

**Pinchtab won't start:**
1. Check port: `curl -s http://localhost:9867/health`
2. Kill stale: `pkill -f pinchtab; pkill -f "\.pinchtab/chrome-profile"`
3. Check logs: pinchtab prints to stderr
4. Clear stale locks: `rm -f ~/.pinchtab/chrome-profile/Singleton*`

**pw daemon won't start:**
1. `pw status` — check browser and daemon
2. `pw close` — kill everything, retry
3. Check `~/.cache/pw-cli/browser.log`
4. `pkill -f "pw-daemon.js"; pkill -f "remote-debugging-port=9222"`

**Headed mode fails (both tools):**
Display access required. Run from a user terminal with WAYLAND_DISPLAY/DISPLAY set, not from agent shell.

<boundaries>
Never work around browser tool failures by launching browser binaries directly, connecting to CDP ports manually, using xdotool, or writing custom websocket/HTTP scripts. Use pinchtab or pw. If both fail, diagnose the underlying issue (port conflict, stale process, missing binary).
</boundaries>
