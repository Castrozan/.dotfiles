<tool_selection>
Browser tools, pick by which session the task needs, not by habit. Default to the user's real everyday session through the stealth CDP target, Chrome DevTools (`mcp__chrome-devtools__*`) on every host, because it carries the user's live logins (Google, Cloudflare Access, banking, anything already signed in) and runs bare so bot detection never sees it; most tasks want exactly that session. PinchTab (`pinchtab` CLI, no MCP) is the deliberate choice for isolated work, never the default reach: its own persistent-profile Chrome, logged in once in headed mode, holding none of the user's real logins, for public scraping, bulk extraction, throwaway browsing, Electron apps, and local or dev sessions the real browser should stay out of. The stealth target is reserved for the interactive session and refuses autonomous clawde agents, so an autonomous agent uses PinchTab regardless. `SKILL.md` holds the per-tool command workflows; this file holds why and when.
</tool_selection>

<stealth_cdp_target_chrome_global>
The stealth target is the chrome-devtools-mcp tool surface pointed at the dedicated Chrome Global profile (`~/.config/chrome-global`) on every host, carrying that browser's own cookies, logins, and extensions. Prefer it when the task needs the user's actual everyday accounts or hits a bot-detecting site (Google, banking, anything behind Cloudflare or PerimeterX); it is the user's real logged-in session, so treat it as the user's own and never clobber the open tab.
</stealth_cdp_target_chrome_global>

<chrome_devtools_is_stealth_by_consent>
The CDP target connects via `--autoConnect` to a real browser launched bare with no `--remote-debugging-port`, no `--enable-automation`, no `navigator.webdriver`. Pages see an ordinary browser carrying the user's real cookies, logins, and profile. The stealth is precisely that consent lives in a live human action, the user's manual Allow on the browser's inspect page (`chrome://inspect`), instead of in a launch flag, so nothing on the page can detect the automation. The Allow gate is the security model and the entire point of this tool, not an obstacle to remove.
</chrome_devtools_is_stealth_by_consent>

<chrome_devtools_never_break_the_gate>
Three traps each waste a whole session if hit: 1) the first `list_pages`, and every new client connection, BLOCKS until the user clicks Allow, which is expected and not a hang, so wait for it and never time it out, retry-storm it, kill the process, or report it broken; 2) never add `--remote-debugging-port` or any automation flag to suppress the prompt, that flag is exactly what destroys the stealth and the recurring manual Allow is the cost of invisibility by design; 3) the target is one browser, single and sequential, so never drive it from parallel agents or open concurrent clients because each new client needs its own Allow and they hang while the browser serializes them, one agent and one connection at a time.
</chrome_devtools_never_break_the_gate>

<real_browser_never_clobber_the_users_open_tab>
The CDP target attaches to a real browser whose selected page on connect is the user's live foreground tab, and `navigate_page` replaces that tab's content in place instead of opening a new one, so navigating the selected tab silently destroys whatever the user had open there. Always open work with `new_page` and `background: true`, which loads a fresh tab without stealing the user's focus, or `select_page` onto a tab you already own; reserve `navigate_page` for a tab you opened yourself. This is intended chrome-devtools-mcp behavior through the latest release, not a bug a version bump fixes, so do not chase a newer pin for it.
</real_browser_never_clobber_the_users_open_tab>

<chrome_devtools_performance_is_not_the_limit>
Once authorized the target sustains tens of thousands of CDP operations per second at roughly 1ms latency with no memory growth, so never diagnose slowness or contention here; the only ceiling is the manual Allow.
</chrome_devtools_performance_is_not_the_limit>

<pinchtab_tradeoffs>
PinchTab is the deliberate choice for isolated work, not the default reach. It runs its own persistent-profile Chrome driven from bash, needs no MCP transport, and a one-time headed login stays authenticated across runs; reach for it when the task wants a profile isolated from the user's real browser - public sites, scraping, research, bulk extraction, throwaway browsing, Electron apps, local or dev sessions - or when an autonomous clawde agent needs a browser at all, since the stealth target refuses it. Its profile is separate from the user's real Chrome, so it holds none of their logins and is not a stealth substitute for bot-detecting sites that need the real session; default to a CDP target there.
</pinchtab_tradeoffs>
</content>
