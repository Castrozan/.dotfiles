<tool_selection>
Three browser tools, pick by detection risk and session needs, not by habit. Browser Use (`mcp__browser-use__*`) is the default for all general browsing. Chrome DevTools (`mcp__chrome-devtools__*`) is only for sites that detect automation and where you need the user's real authenticated session: Google, banking, anything behind Cloudflare or PerimeterX. PinchTab (`pinchtab` CLI, no MCP) is the fallback when the MCP transports go flaky or you need a persistent already-logged-in local or dev session. `SKILL.md` holds the per-tool command workflows; this file holds why and when.
</tool_selection>

<chrome_devtools_is_stealth_by_consent>
Chrome DevTools connects via `--autoConnect` to the user's real Chrome Global, launched bare with no `--remote-debugging-port`, no `--enable-automation`, no `navigator.webdriver`. Pages see an ordinary browser carrying the user's real cookies, logins, and profile. The stealth is precisely that consent lives in a live human action, the user's manual Allow on `chrome://inspect`, instead of in a launch flag, so nothing on the page can detect the automation. The Allow gate is the security model and the entire point of this tool, not an obstacle to remove.
</chrome_devtools_is_stealth_by_consent>

<chrome_devtools_never_break_the_gate>
Three traps each waste a whole session if hit: 1) the first `list_pages`, and every new client connection, BLOCKS until the user clicks Allow, which is expected and not a hang, so wait for it and never time it out, retry-storm it, kill the process, or report it broken; 2) never add `--remote-debugging-port` or any automation flag to suppress the prompt, that flag is exactly what destroys the stealth and the recurring manual Allow is the cost of invisibility by design; 3) it is one Chrome Global, single and sequential, so never drive it from parallel agents or open concurrent clients because each new client needs its own Allow and they hang while Chrome serializes them, one agent and one connection at a time.
</chrome_devtools_never_break_the_gate>

<chrome_devtools_performance_is_not_the_limit>
Once authorized it sustains tens of thousands of CDP operations per second at roughly 1ms latency with no memory growth, so never diagnose slowness or contention here; the only ceiling is the manual Allow.
</chrome_devtools_performance_is_not_the_limit>

<browser_use_and_pinchtab_tradeoffs>
Browser Use launches its own Chrome, needs zero setup, and supports parallel sessions, but it carries automation flags so bot-detecting sites flag it; use it for public sites, scraping, research, bulk extraction, throwaway browsing, and Electron apps. PinchTab runs its own persistent-profile Chrome driven from bash, so a one-time headed login stays authenticated across runs and it survives MCP flakiness, but its profile is separate from the user's real Chrome so it is not a stealth substitute for bot-detecting sites.
</browser_use_and_pinchtab_tradeoffs>
