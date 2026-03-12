---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

<architecture>
Pinchtab runs Chrome behind an HTTP API at localhost:9867. Two modes: headless (default) and headed (visible window for login flows, CAPTCHAs, verification). Cookies persist across restarts and mode switches. After user logs in via headed mode, switch back to headless — the session carries over.
</architecture>

<startup_traps>
Run pinchtab-ensure-running or pinchtab-switch-mode with run_in_background: true. Health-check separately after startup — sleep 4 seconds then hit the health endpoint.

The Bash tool sandbox sends SIGUSR2 to background processes, producing exit code 144. This is expected — not an error. Only trust the health endpoint for status. Run each pinchtab step as a separate Bash call — never chain with `&&` or `;`, as exit 144 from one command aborts the chain.
</startup_traps>

<interaction_paradigm>
Every browser interaction is one tool call. Four helper scripts handle the navigate/act/wait/snapshot cycle:

pinchtab-navigate-and-snapshot: navigates to URL, waits for page stabilization, returns interactive elements with `eN` refs. pinchtab-act-and-snapshot: executes an action JSON, returns only what changed as a diff. pinchtab-screenshot: captures page image to a file path. pinchtab-fill-form: fills form fields via CSS selectors and JavaScript injection.

The default flow: navigate to discover elements → act with diff to see changes → escalate to interactive filter only when diff shows new elements appeared.
</interaction_paradigm>

<action_traps>
`fill`, `type`, and `select` ref-based actions silently fail on most forms (both SPA and plain HTML). `click` on checkbox/radio refs does not toggle state. Always use pinchtab-fill-form for form input — it uses CSS selectors (not eN refs) and JavaScript evaluate to bypass framework reactivity issues.

pinchtab-navigate-and-snapshot calls /navigate which reloads the page — any filled form data is lost. To re-discover elements without losing form state, use pinchtab-act-and-snapshot with a no-op action and filter=interactive query param.

For search forms, skip the form entirely — navigate directly with query params in the URL.
</action_traps>

<observation_costs>
Diff snapshot (~500 tokens) is the default after actions. Page text via /text endpoint (~800 tokens) for reading content. Screenshot (~1,500 tokens) for visual verification. Interactive filter (~3,600 tokens) for discovering elements. Full /snapshot (~10,000 tokens) rarely needed.

Batch form fills instead of one-field-at-a-time. Skip observation for predictable outcomes (closing modals, pressing Enter). For 3+ actions with known outcomes, chain acts then observe once at the end.
</observation_costs>

<complex_automation>
For sequences exceeding 10 browser actions, write a dedicated JavaScript script using the CDP pattern from the ponto skill's scripts. Connect directly to Chrome's WebSocket debug port, execute all DOM interactions in a single script, return structured results.
</complex_automation>

<troubleshooting>
Pinchtab won't start: graceful shutdown via the shutdown endpoint, clear Chrome lock files in profile directory, check log. Bot detection: BRIDGE_STEALTH=full env var on startup. Tab API supports new and close only — no tab switching.
</troubleshooting>
