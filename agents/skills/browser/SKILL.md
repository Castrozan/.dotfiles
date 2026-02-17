---
name: browser
description: Use when user asks to open a webpage, scrape content, fill forms, click buttons, take screenshots, test a web UI, or automate any browser interaction. Also use when navigating authenticated web apps or testing frontend changes.
---

# Browser Automation

## Setup

The agent browser uses Chromium with a dedicated profile (`~/.local/share/pw-browser/`). The browser launches with AI-friendly flags: notifications disabled, no translate prompts, no password manager popups, English locale for consistent element labels.

Sessions and logins persist across reboots and across headless/headed mode switches.

### Logged-in Sites

The user has already logged into most of these sites in the browser profile, so try accessing them first to confirm:
- **Google/YouTube/...** — `pw open https://accounts.google.com --headed` if not yet done

### One-time Login (when needed)

For sites requiring manual auth (QR codes, 2FA), ask the user to log in via headed mode:

```bash
pw open https://web.whatsapp.com --headed   # User scans QR code
pw open https://github.com/login --headed   # User enters credentials
```

## pw CLI (Primary — ~400ms per command)

Persistent browser. Browser stays alive between commands.

### Workflow

```bash
pw open https://example.com     # Navigate (auto-starts headless browser)
pw elements                     # Interactive elements with [index]
pw click 3                      # Click by index
pw snap                         # Accessibility tree (YAML)
pw fill "input[name=q]" hello   # Fill form field
pw screenshot                   # Save screenshot
pw close                        # Kill agent browser
```

### Commands

`pw help`: Show help information

### Element Interaction Pattern

```bash
pw elements                      # See: [0] <a -> /about> About  [1] <button #submit> Go
pw click 0                       # Click "About" link by index
pw fill "input[name=email]" x    # Fill by CSS selector
pw click "#submit"               # Click by CSS selector
```

### Headed Mode (visible browser)

Use `--headed` to launch a visible browser window while retaining full CDP control. The user sees the browser on screen while you operate it programmatically.

```bash
pw open https://x.com/home --headed   # Launches visible Chromium + CDP control
pw elements                            # Works normally against the visible window
pw click 5                             # User watches the click happen
pw open https://youtube.com            # Navigate — same window, user sees it
```

If a headless browser is already running, `--headed` restarts it in visible mode automatically. The `PW_HEADED=true` env var also works.

### Example: Multi-site Navigation

```bash
# Open x.com, find and click the first post
pw open https://x.com/home --headed
sleep 2                                          # Wait for feed to load
pw elements | grep "article\|status/"            # Find post links
pw click 41                                      # Click post by index

# Navigate to YouTube, click first video
pw open https://www.youtube.com
sleep 1                                          # Wait for thumbnails
pw elements | grep "<a.*watch" | head -5         # Find video links
pw click 103                                     # Click video by index
```

### Tips

- Use `pw snap` for semantic page understanding, `pw elements` for clickable targets
- `pw eval "document.querySelector('selector')?.click()"` bypasses Playwright actionability checks when elements are behind overlays
- `pw scroll down 800` to load more content on infinite-scroll pages
- `sleep 1-2` after navigation on JS-heavy sites (x.com, YouTube) before querying elements

### Performance

- Cold start (browser launch): ~1s
- Each command after: ~400ms (350ms Node.js load + 50ms CDP + operation)
- Operations themselves: 2-50ms

## Troubleshooting

When `pw` fails, diagnose with these steps in order:

1. Run `pw status` to check if browser and daemon are alive
2. Run `pw close` then retry the original command (kills stale processes)
3. Check browser log at `~/.cache/pw-cli/browser.log` for crash details
4. Kill orphan processes: `pkill -f remote-debugging-port=9222; pkill -f pw-daemon.js`
5. If the error mentions "No browser found in PATH", install chromium via nix (`nix-env -iA nixpkgs.chromium` or add to home-manager config)

Common errors and fixes:
- **"daemon not responding"** → daemon crashed or never started. Run `pw close` and retry.
- **"No page open"** → run `pw open <url>` before other commands.
- **"Failed to start agent browser"** → browser binary crashes on launch. Check `~/.cache/pw-cli/browser.log` for details. Port conflict is another cause — check if something else uses port 9222.
- **Headed mode fails** → display server not available. Verify DISPLAY or WAYLAND_DISPLAY environment variables are set.

<boundaries>
Never work around pw failures by launching browser binaries directly, connecting to CDP ports manually, using xdotool, or writing custom websocket/HTTP scripts. The pw tool manages its own browser lifecycle. If pw cannot start the browser, the fix is in pw's configuration or the system environment — not in bypassing pw. Follow the troubleshooting steps above, check the browser log, fix the underlying issue (missing binary, port conflict, display env), and retry.
</boundaries>

## Chrome DevTools MCP (Frontend Development & Fallback)

Configured as Claude Code MCP server via `chrome-devtools-mcp`. Connects to Chrome via CDP and exposes DevTools capabilities that `pw` does not cover.

### When to Use

Use `pw` (above) for **most browser automation**: navigation, clicking, filling forms, screenshots, accessibility snapshots. It's faster and simpler.

Use **Chrome DevTools MCP** when you need:
- **Network monitoring** — inspect requests, responses, headers, timing waterfall
- **Performance profiling** — runtime performance traces, Core Web Vitals, CrUX field data
- **Device/network emulation** — simulate mobile viewports, slow 3G, offline mode
- **Console access** — read console logs, warnings, errors from the page
- **CSS coverage** — identify unused CSS rules
- **Frontend debugging** — anything you'd normally do in the Chrome DevTools panels

### Available Tool Categories

- **Network** — monitor requests, intercept traffic, check response headers
- **Performance** — capture traces, analyze rendering, measure load times
- **Emulation** — device simulation, geolocation, network throttling
- **Core browser** — navigate, screenshot, evaluate JS, interact with elements

### Connection Modes

The MCP server can connect to `pw`'s browser instance (same CDP port 9222) or launch its own:

```bash
# Standalone (default config — launches its own headless Chrome)
# Already configured in ~/.claude/mcp.json

# Connect to pw's running browser
chrome-devtools-mcp --browserUrl http://127.0.0.1:9222
```

### Tips

- For simple automation (click, fill, navigate), prefer `pw` — it's faster
- For debugging frontend issues, network analysis, or performance profiling, use the MCP tools
- Both tools can share the same Chrome profile at `~/.local/share/pw-browser/`
