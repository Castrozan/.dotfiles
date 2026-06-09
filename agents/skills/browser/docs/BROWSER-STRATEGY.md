# Browser Automation Strategy

Three tools, different strengths. Browser Use is the default; Chrome DevTools MCP is for stealth; PinchTab is the CLI fallback when the MCP transports are flaky or you need a stable already-authenticated local session.

## Browser Use MCP - primary, general purpose

Default tool for all browser automation. Launches its own Chrome instance, works immediately with no setup. Use for public websites, scraping, research, bulk extraction, parallel browser sessions, quick throwaway browsing, and any task where bot detection is not a concern. Also handles Electron app automation via CDP connection.

## Chrome DevTools MCP - stealth, authenticated sites

Connects to the user's real Chrome Global which runs bare with zero automation flags. Google and other bot-detecting services see a normal browser because there are no `--remote-debugging-port`, `--enable-automation`, or `navigator.webdriver` flags. The consent dialog the user clicks is the security model that makes the connection invisible to websites.

Use exclusively for Google Workspace, sites behind Cloudflare/PerimeterX bot detection, and any authenticated session where detection means account lock. Real cookies, real logins, real profile.

Tradeoff: single Chrome Global instance, sequential. Requires user to have remote debugging enabled in Chrome.

## PinchTab CLI - resilient fallback, persistent auth

No MCP - a `pinchtab` binary driven from bash, so it keeps working when an MCP server is flaky or disconnected mid-session. Runs its own server on `localhost:9867` with a persistent Chrome profile, so a one-time headed login stays authenticated across runs - it renders authed local apps (e.g. a CA3-backed dev server) without re-login.

Reach for it when: the MCP tools are flaky or disconnected, you need a stable already-logged-in session for a local/dev app, or you want screenshot/snapshot verification driven entirely from the shell. Core loop: `pinchtab nav <url>` -> `pinchtab snap` (a11y refs, prefer over pixels) -> `pinchtab screenshot --output <file>` then Read the file; interact with `pinchtab click <ref>` / `type <ref> <text>`; `pinchtab server -H` for a visible window to log in. See the skill's `pinchtab_workflow` for the command list.

Tradeoff: guards are UP by default (only localhost/127.0.0.1 allowed; `server -y` lowers them); its profile is separate from the user's real Chrome, so it is not a stealth substitute for bot-detecting sites.

## Decision matrix

| Scenario | Tool |
|---|---|
| Default / general browsing | Browser Use |
| Public scraping, research, bulk extraction | Browser Use |
| Electron app automation | Browser Use |
| Parallel browser sessions | Browser Use |
| Google services, banking, authenticated sites | Chrome DevTools MCP |
| Sites with aggressive bot detection + need local auth | Chrome DevTools MCP |
| MCP transport flaky / disconnected mid-task | PinchTab CLI |
| Authed local/dev app, want a session that stays logged in | PinchTab CLI |
| Shell-driven screenshot/snapshot verification | PinchTab CLI |
