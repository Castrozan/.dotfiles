---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

<architecture>
Three-tier browser access, choose based on task:

1. **chrome-devtools-live MCP** (primary) — attaches to user's real Chrome via autoConnect. Real logins, real cookies, no automation detection. Use for authenticated sites, logged-in workflows, anything needing real session state. Requires Chrome running with remote debugging enabled at chrome://inspect/#remote-debugging.

2. **agent-browser CLI** (secondary) — native Rust CLI, 150+ commands, 200-400 tokens per snapshot (vs 3000-5000 for full DOM). Use for token-efficient automation, quick scraping, form filling, screenshots. No MCP — run via Bash tool directly.

3. **Pinchtab HTTP API** (fallback) — Chrome behind HTTP API at localhost:9867. Use for complex form automation via CSS selectors + JS injection, batch actions, and when the above two are unavailable.
</architecture>

<tier_selection>
Use chrome-devtools-live when: site requires login (banking, email, dashboards, admin panels), site blocks headless/automation browsers, need access to existing tabs/sessions.

Use agent-browser when: scraping public pages, filling simple forms, taking screenshots, reading page content, token budget is tight, tasks need chained browser commands.

Use Pinchtab when: forms use React/Vue reactivity that breaks standard fill (use pinchtab-fill-form with CSS selectors), need batch form fills, need the HTTP API for programmatic control, chrome-devtools-live is unavailable.
</tier_selection>

<chrome_devtools_live>
The chrome-devtools-live MCP server connects to the user's running Chrome via Model Context Protocol. Key tools: navigate_page, click, fill, fill_form, take_screenshot, take_snapshot, evaluate_script, list_pages, new_page, select_page, wait_for, press_key, hover, drag, upload_file, handle_dialog.

Chrome must be running with remote debugging enabled. Each connection requires user approval via Chrome's permission dialog. A yellow banner shows "Chrome is being controlled by automated test software" during active sessions.

When chrome-devtools-live fails to connect: verify Chrome is running, check chrome://inspect/#remote-debugging is enabled, look for the permission dialog in Chrome.
</chrome_devtools_live>

<agent_browser>
agent-browser is a native Rust CLI. Core workflow: open URL → snapshot -i (get interactive elements with @ref tags) → interact using refs → re-snapshot after DOM changes.

Essential commands:
- `agent-browser open <url>` — navigate to URL
- `agent-browser snapshot -i` — get interactive elements with @e1, @e2 refs (200-400 tokens)
- `agent-browser click @e1` — click element by ref
- `agent-browser fill @e2 "text"` — fill input field
- `agent-browser type "text"` — type text at cursor
- `agent-browser press Enter` — press key
- `agent-browser screenshot` — capture page image
- `agent-browser get text` — get page text content
- `agent-browser get url` — get current URL
- `agent-browser wait networkidle` — wait for network to settle
- `agent-browser eval "document.title"` — execute JavaScript

Auto-connect to running Chrome: `agent-browser --auto-connect open <url>` or set `AGENT_BROWSER_AUTO_CONNECT=1`.

Commands can be chained: `agent-browser open <url> && agent-browser snapshot -i`

For parallel sessions: `agent-browser --session myname open <url>`

Security: restrict domains with `AGENT_BROWSER_ALLOWED_DOMAINS=example.com,api.example.com`
</agent_browser>

<pinchtab_fallback>
Pinchtab runs Chrome behind an HTTP API at localhost:9867. Two modes: headless (default) and headed (visible window for login flows, CAPTCHAs).

Startup: run pinchtab-ensure-running with run_in_background: true. Health-check separately — sleep 4 seconds then hit the health endpoint. The Bash tool sandbox sends SIGUSR2 to background processes producing exit code 144 — this is expected. Run each pinchtab step as a separate Bash call.

Four helper scripts: pinchtab-navigate-and-snapshot (navigate + wait + snapshot with eN refs), pinchtab-act-and-snapshot (action + diff), pinchtab-screenshot (capture image), pinchtab-fill-form (CSS selectors + JS injection for framework-resistant form filling).

Key trap: fill/type/select ref-based actions silently fail on most forms. Always use pinchtab-fill-form for form input — it uses CSS selectors and JavaScript evaluate to bypass React/Vue reactivity.
</pinchtab_fallback>

<observation_costs>
agent-browser snapshot: ~200-400 tokens (accessibility tree with refs). Pinchtab diff: ~500 tokens. Page text: ~800 tokens. Screenshot: ~1,500 tokens. Pinchtab interactive filter: ~3,600 tokens. Full DOM snapshot: ~10,000 tokens.

Prefer agent-browser snapshots when token budget matters. Batch form fills. Skip observation for predictable outcomes.
</observation_costs>

<complex_automation>
For sequences exceeding 10 browser actions, write a dedicated JavaScript script using CDP. Connect directly to Chrome's WebSocket debug port, execute all DOM interactions in a single script, return structured results. See ponto skill scripts for the CDP pattern.
</complex_automation>
