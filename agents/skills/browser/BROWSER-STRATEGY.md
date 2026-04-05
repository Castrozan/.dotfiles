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

Chrome Global runs bare with zero automation flags. The user launches it via SUPER+C (`hypr-summon-chrome-global`) and enables remote debugging once via `chrome://inspect/#remote-debugging` (toggle persists across restarts). The consent dialog must be clicked Allow once per Chrome session. The MCP connects via `--autoConnect` which discovers Chrome through the user data directory. Google and other bot-detecting services see a normal browser because there are no `--remote-debugging-port`, `--enable-automation`, or `navigator.webdriver` flags.

Use exclusively for Google Workspace, sites behind Cloudflare/PerimeterX bot detection, and any authenticated session where detection means account lock. Real cookies, real logins, real profile.

Tradeoff: single Chrome Global instance, sequential. User must launch Chrome and have remote debugging toggled on.

## Decision matrix

| Scenario | Tool |
|---|---|
| Default / general browsing | Browser Use |
| Public scraping, research, bulk extraction | Browser Use |
| Electron app automation | Browser Use (`--cdp-url`) |
| Parallel browser sessions | Browser Use |
| Google services, banking, authenticated sites | Chrome DevTools MCP |
| Sites with aggressive bot detection + need local auth | Chrome DevTools MCP |
