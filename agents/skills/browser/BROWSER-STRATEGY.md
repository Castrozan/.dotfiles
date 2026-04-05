# Browser Automation Strategy

Two tools, different strengths. Browser Use is the default; Chrome DevTools MCP is for stealth.

## Browser Use MCP - primary, general purpose

Default tool for all browser automation. Launches its own Chrome instance, works immediately with no setup. Use for public websites, scraping, research, bulk extraction, parallel browser sessions, quick throwaway browsing, and any task where bot detection is not a concern. Also handles Electron app automation via CDP connection.

## Chrome DevTools MCP - stealth, authenticated sites

Connects to the user's real Chrome Global which runs bare with zero automation flags. Google and other bot-detecting services see a normal browser because there are no `--remote-debugging-port`, `--enable-automation`, or `navigator.webdriver` flags. The consent dialog the user clicks is the security model that makes the connection invisible to websites.

Use exclusively for Google Workspace, sites behind Cloudflare/PerimeterX bot detection, and any authenticated session where detection means account lock. Real cookies, real logins, real profile.

Tradeoff: single Chrome Global instance, sequential. Requires user to have remote debugging enabled in Chrome.

## Decision matrix

| Scenario | Tool |
|---|---|
| Default / general browsing | Browser Use |
| Public scraping, research, bulk extraction | Browser Use |
| Electron app automation | Browser Use |
| Parallel browser sessions | Browser Use |
| Google services, banking, authenticated sites | Chrome DevTools MCP |
| Sites with aggressive bot detection + need local auth | Chrome DevTools MCP |
