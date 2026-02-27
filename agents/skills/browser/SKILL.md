---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

<helper-scripts>
Always prefer these over raw commands — they handle edge cases and are idempotent.

- `pinchtab-ensure-running` — start headless pinchtab if not already running. Idempotent. Use with `run_in_background: true`.
- `pinchtab-switch-mode [headless|headed]` — kill existing instance, clear locks, relaunch in specified mode. Use with `run_in_background: true`.
- `pinchtab-screenshot [output-path]` — capture screenshot, decode base64, validate image. Default path: `/tmp/screenshot.jpg`. Then Read the output file. Never call the `/screenshot` API directly with curl.
</helper-scripts>

<startup>
Pinchtab runs Chrome behind an HTTP API at localhost:9867. Two modes: headless (default) and headed (user sees the browser window). Use headed mode when the user needs to see or interact with the browser — login flows, verification codes, CAPTCHAs, or when user explicitly asks to open a page visibly. You can launch either mode yourself.

Headless startup: run `pinchtab-ensure-running` with `run_in_background: true` and `timeout: 120000`. It is idempotent — exits if already running. Then health-check separately: `sleep 4 && curl -sf --max-time 3 http://localhost:9867/health`.

Headed startup or mode switch: run `pinchtab-switch-mode headed` with `run_in_background: true`. It kills any existing instance, clears locks, and launches in headed mode. Then health-check separately: `sleep 5 && curl -sf --max-time 3 http://localhost:9867/health`. Switch back with `pinchtab-switch-mode headless`.

Cookies persist in `~/.pinchtab/chrome-profile/` across restarts and mode switches. After user logs in via headed mode, switch back to headless — the session carries over.
</startup>

<sandbox-behavior>
The Bash tool sandbox sends SIGUSR2 to background processes, producing exit code 144. This is normal and expected — not an error. Never interpret exit code 144 as a failure. The only reliable way to check pinchtab status is the health endpoint. Run each step as a separate Bash call — never chain pinchtab commands with `&&` or `;`, as exit code 144 from one command aborts the chain.
</sandbox-behavior>

<core-pattern>
Navigate, then read or snapshot, then act.

```bash
curl -s -X POST http://localhost:9867/navigate -H "Content-Type: application/json" -d '{"url":"https://example.com"}'

curl -s http://localhost:9867/text | python3 -c "import sys,json; print(json.load(sys.stdin).get('text',''))"

curl -s "http://localhost:9867/snapshot?filter=interactive&format=compact"

curl -s -X POST http://localhost:9867/action -H "Content-Type: application/json" -d '{"kind":"click","ref":"e5"}'

curl -s -X POST http://localhost:9867/action -H "Content-Type: application/json" -d '{"kind":"fill","ref":"e3","text":"query"}'

curl -s -X POST http://localhost:9867/action -H "Content-Type: application/json" -d '{"kind":"press","key":"Enter"}'

curl -s -X POST http://localhost:9867/evaluate -H "Content-Type: application/json" -d '{"expression":"document.title"}'
```

Prefer `/text` (~800 tokens) when only reading. Use `?filter=interactive` (~3,600 tokens) when you need to act. Full snapshot (~10,000 tokens) only when page structure matters.
</core-pattern>

<action-reference>
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

`fill` replaces input content. `type` appends characters. Snapshot filters: `?filter=interactive`, `?selector=CSS`, `?diff=true`, `?depth=N`.
</action-reference>

<tabs-and-sessions>
Tab API supports `new` and `close` only — no tab activation. Navigate within the active tab.
</tabs-and-sessions>

<troubleshooting>
Pinchtab won't start: kill stale processes (`pkill -f pinchtab`), clear locks (`rm -f ~/.pinchtab/chrome-profile/Singleton*`), check `/tmp/pinchtab.log`.

Bot detection / CAPTCHA: set `BRIDGE_STEALTH=full` env var on startup. Pinchtab patches `navigator.webdriver` by default but some sites need full canvas/WebGL spoofing.
</troubleshooting>
