# Browser Automation Strategy

Two tools, different strengths. Browser Use is the default; Chrome DevTools MCP is for stealth.

## Browser Use MCP (primary — general purpose)

Default tool for all browser automation. Launches its own Chrome instance via the `browser-use` MCP server (stdio transport). Configured with `executable_path` pointing to the Nix Chrome binary so it works on NixOS.

Use for:
- Public websites, scraping, research, bulk extraction
- Electron apps (connect via `--cdp-url` to any app launched with `--remote-debugging-port`)
- Parallel browser sessions
- Quick throwaway browsing, no login needed
- Any task where bot detection is not a concern

Tools: `browser_navigate`, `browser_click`, `browser_type`, `browser_get_state`, `browser_screenshot`, `browser_extract_content`, `browser_scroll`, `browser_go_back`, `browser_list_tabs`, `browser_switch_tab`, `browser_close_tab`, `browser_get_html`, `browser_list_sessions`, `browser_close_session`, `browser_close_all`.

### Avoiding detection issues

When targeting sites with basic bot detection:
- Use `--profile` flag to connect to a real Chrome profile with existing cookies
- Connect to the user's running Chrome via `--cdp-url` instead of launching a new instance
- Use `--connect` to auto-discover a running Chrome's CDP port

### Electron apps

Any Electron app exposes CDP when launched with `--remote-debugging-port=<port>`. Connect Browser Use to it:
```
browser-use --cdp-url http://localhost:<port> state
```
Works with VS Code, Discord, Obsidian, MongoDB Compass, or any Electron-based app.

## Chrome DevTools MCP (stealth — authenticated sites)

Connects to the user's real Chrome Global via DevToolsActivePort. No automation flags, no `--enable-automation`, no `navigator.webdriver=true`. The acceptance dialog is intentional — it proves Chrome was launched normally, not by an automation framework.

Google, banking sites, and any service that fingerprints CDP/automation flags see a normal human browser. Real cookies, real logins, real profile. This is the only tool for:
- Google Workspace (Gmail, Calendar, Drive, Chat)
- Sites behind Cloudflare/PerimeterX bot detection
- Any authenticated session where detection = account lock

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
