# Browser Automation Strategy

Two tools, different strengths. Browser Use is the default; Chrome DevTools MCP is for stealth.

## Browser Use MCP - primary, general purpose

Default tool for all browser automation. Launches its own Chrome instance via the browser-use MCP server (stdio transport). Configured with `executable_path` pointing to the Nix Chrome binary so it works on NixOS.

Use for public websites, scraping, research, bulk extraction, parallel browser sessions, quick throwaway browsing, and any task where bot detection is not a concern. Also handles Electron app automation via CDP connection.

### Avoiding detection

When targeting sites with basic bot detection, use `--profile` to connect to a real Chrome profile with existing cookies, `--cdp-url` to attach to the user's running Chrome instead of launching a new instance, or `--connect` to auto-discover a running Chrome's CDP port.

### Electron apps

Any Electron app exposes CDP when launched with `--remote-debugging-port=<port>`. Connect Browser Use to it with `browser-use --cdp-url http://localhost:<port> state`. Works with VS Code, Discord, Obsidian, MongoDB Compass, or any Electron-based app.

## Chrome DevTools MCP - stealth, authenticated sites

Connects to the user's real Chrome Global via DevToolsActivePort. No automation flags, no `--enable-automation`, no `navigator.webdriver=true`. The acceptance dialog is intentional - it proves Chrome was launched normally, not by an automation framework.

Google, banking sites, and any service that fingerprints CDP/automation flags see a normal human browser with real cookies, real logins, and a real profile. Use exclusively for Google Workspace, sites behind Cloudflare/PerimeterX bot detection, and any authenticated session where detection means account lock.

Tradeoff: requires a running Chrome Global on the local machine. Single instance, sequential.

## Decision matrix

| Scenario | Tool |
|---|---|
| Default / general browsing | Browser Use |
| Public scraping, research, bulk extraction | Browser Use |
| Electron app automation | Browser Use (`--cdp-url`) |
| Parallel browser sessions | Browser Use |
| Google services, banking, authenticated sites | Chrome DevTools MCP |
| Sites with aggressive bot detection + need local auth | Chrome DevTools MCP |
