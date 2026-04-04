# Browser Automation Strategy

Two tools, different strengths. Browser Use is the default; Chrome DevTools MCP is for stealth.

## Browser Use MCP - primary, general purpose

Default tool for all browser automation. Launches its own Chrome instance via the browser-use MCP server (stdio transport). The system Chrome binary is configured via `executable_path` in `~/.config/browseruse/config.json`.

Use for public websites, scraping, research, bulk extraction, parallel browser sessions, quick throwaway browsing, and any task where bot detection is not a concern. Also handles Electron app automation via CDP connection.

### Avoiding detection

When targeting sites with basic bot detection, use `--profile` to connect to a real Chrome profile with existing cookies, `--cdp-url` to attach to the user's running Chrome instead of launching a new instance, or `--connect` to auto-discover a running Chrome's CDP port.

### Electron apps

Any Electron app exposes CDP when launched with `--remote-debugging-port=<port>`. Connect Browser Use to it with `browser-use --cdp-url http://localhost:<port> state`. Works with VS Code, Discord, Obsidian, MongoDB Compass, or any Electron-based app.

## Chrome DevTools MCP - stealth, authenticated sites

Fully automated from zero. The MCP wrapper handles the entire lifecycle: launches Chrome bare (no `--remote-debugging-port`, no automation flags), opens `chrome://inspect/#remote-debugging` to enable the internal debug server, auto-accepts the consent dialog via the consent acceptor script, then connects via `--autoConnect`. Google and other bot-detecting services see a normal browser because there are no automation flags - the consent dialog proves human-level approval and makes the connection invisible to websites.

Use exclusively for Google Workspace, sites behind Cloudflare/PerimeterX bot detection, and any authenticated session where detection means account lock. Real cookies, real logins, real profile.

Tradeoff: single Chrome Global instance, sequential. The consent dialog is auto-accepted once per session.

## Decision matrix

| Scenario | Tool |
|---|---|
| Default / general browsing | Browser Use |
| Public scraping, research, bulk extraction | Browser Use |
| Electron app automation | Browser Use (`--cdp-url`) |
| Parallel browser sessions | Browser Use |
| Google services, banking, authenticated sites | Chrome DevTools MCP |
| Sites with aggressive bot detection + need local auth | Chrome DevTools MCP |
