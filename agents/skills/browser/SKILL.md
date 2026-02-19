---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

# Browser Automation

Headless Chrome via HTTP API at `localhost:9867`. Two helper scripts handle startup and screenshots.

<startup>
Run `pinchtab-ensure-running` with `run_in_background: true` and `timeout: 120000`. It is idempotent — exits immediately if already running, otherwise starts pinchtab and blocks.

Then health-check in a separate Bash call:

```bash
sleep 4 && curl -sf --max-time 3 http://localhost:9867/health
```

Exit code 144 from the Bash tool is normal (shell sandbox signal). Health-check separately to confirm.
</startup>

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

<screenshots>
Run `pinchtab-screenshot /tmp/screenshot.jpg`, then Read the file. The script decodes base64 and validates the image. Never call `/screenshot` directly with curl — it returns JSON, not bytes. Reading invalid JSON as an image poisons the conversation permanently.
</screenshots>

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

Cookies persist in `~/.pinchtab/chrome-profile/` across restarts. For manual login, user runs `BRIDGE_HEADLESS=false pinchtab` from their terminal.
</tabs-and-sessions>

<troubleshooting>
Pinchtab won't start: kill stale processes (`pkill -f pinchtab`), clear locks (`rm -f ~/.pinchtab/chrome-profile/Singleton*`), check `/tmp/pinchtab.log`.

Bot detection / CAPTCHA: try `BRIDGE_STEALTH=full` env var on startup. Pinchtab patches `navigator.webdriver` by default but some sites need full canvas/WebGL spoofing.
</troubleshooting>
