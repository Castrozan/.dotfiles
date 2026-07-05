<tool_selection>
Browser tools, pick by detection risk and which session you need, not by habit. Browser Use (`mcp__browser-use__*`) is the default for all general browsing. The three stealth CDP targets, Chrome DevTools (`mcp__chrome-devtools__*`), Brave DevTools (`mcp__brave-devtools__*`), and Vivaldi DevTools (`mcp__vivaldi-devtools__*`), are only for sites that detect automation and where you need a real authenticated session: Google, banking, anything behind Cloudflare or PerimeterX. PinchTab (`pinchtab` CLI, no MCP) is the fallback when the MCP transports go flaky or you need a persistent already-logged-in local or dev session. `SKILL.md` holds the per-tool command workflows; this file holds why and when.
</tool_selection>

<stealth_cdp_targets_chrome_brave_vivaldi>
The stealth targets are the same chrome-devtools-mcp tool surface pointed at a different browser, so choose by which browser actually holds the logged-in session you need. `mcp__chrome-devtools__*` attaches to the dedicated Chrome Global profile (`~/.config/chrome-global`); `mcp__brave-devtools__*` attaches to the user's real everyday Brave, the one Cmd+B summons, on its default profile (`~/Library/Application Support/BraveSoftware/Brave-Browser` on darwin, `~/.config/BraveSoftware/Brave-Browser` on linux); `mcp__vivaldi-devtools__*` attaches to the native Vivaldi on its default profile (`~/Library/Application Support/Vivaldi` on darwin, `~/.config/vivaldi` on linux); each carries that browser's own cookies, logins, and extensions. Prefer Brave when the task needs the user's actual everyday accounts and is a Google or other Chromium-friendly site; the targets are independent browsers, never assume a login in one exists in the others.
</stealth_cdp_targets_chrome_brave_vivaldi>

<chrome_devtools_is_stealth_by_consent>
The CDP targets connect via `--autoConnect` to a real browser launched bare with no `--remote-debugging-port`, no `--enable-automation`, no `navigator.webdriver`. Pages see an ordinary browser carrying the user's real cookies, logins, and profile. The stealth is precisely that consent lives in a live human action, the user's manual Allow on the browser's inspect page (`chrome://inspect` for the Chrome target, `brave://inspect` for the Brave target, `vivaldi://inspect` for the Vivaldi target), instead of in a launch flag, so nothing on the page can detect the automation. The Allow gate is the security model and the entire point of these tools, not an obstacle to remove.
</chrome_devtools_is_stealth_by_consent>

<chrome_devtools_never_break_the_gate>
Three traps each waste a whole session if hit, and they apply to each target independently: 1) the first `list_pages`, and every new client connection, BLOCKS until the user clicks Allow, which is expected and not a hang, so wait for it and never time it out, retry-storm it, kill the process, or report it broken; 2) never add `--remote-debugging-port` or any automation flag to suppress the prompt, that flag is exactly what destroys the stealth and the recurring manual Allow is the cost of invisibility by design; 3) each target is one browser, single and sequential, so never drive it from parallel agents or open concurrent clients because each new client needs its own Allow and they hang while the browser serializes them, one agent and one connection at a time per target.
</chrome_devtools_never_break_the_gate>

<real_browser_never_clobber_the_users_open_tab>
The CDP targets attach to a real browser whose selected page on connect is the user's live foreground tab, and `navigate_page` replaces that tab's content in place instead of opening a new one, so navigating the selected tab silently destroys whatever the user had open there. Always open work with `new_page` and `background: true`, which loads a fresh tab without stealing the user's focus, or `select_page` onto a tab you already own; reserve `navigate_page` for a tab you opened yourself. This is intended chrome-devtools-mcp behavior through the latest release, not a bug a version bump fixes, so do not chase a newer pin for it.
</real_browser_never_clobber_the_users_open_tab>

<chrome_devtools_performance_is_not_the_limit>
Once authorized any target sustains tens of thousands of CDP operations per second at roughly 1ms latency with no memory growth, so never diagnose slowness or contention here; the only ceiling is the manual Allow.
</chrome_devtools_performance_is_not_the_limit>

<browser_use_and_pinchtab_tradeoffs>
Browser Use launches its own Chrome, needs zero setup, and supports parallel sessions, but it carries automation flags so bot-detecting sites flag it; use it for public sites, scraping, research, bulk extraction, throwaway browsing, and Electron apps. PinchTab runs its own persistent-profile Chrome driven from bash, so a one-time headed login stays authenticated across runs and it survives MCP flakiness, but its profile is separate from the user's real Chrome so it is not a stealth substitute for bot-detecting sites.
</browser_use_and_pinchtab_tradeoffs>
