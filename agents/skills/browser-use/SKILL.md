---
name: browser-use
description: Automates browser interactions for web testing, form filling, screenshots, and data extraction. Use when the user needs to navigate websites, interact with web pages, fill forms, take screenshots, or extract information from web pages.
allowed-tools: Bash(browser-use:*)
---

<!-- TODO: Browser automation needs a definitive consolidated approach.
     Test all 3 tools (browser-use, playwright, playwright-mcp), pick the fastest/most reliable,
     consolidate into one canonical skill. Track: which works best for OpenClaw's use case
     (auth sites, form filling, scraping). -->

# Browser Automation with browser-use CLI

The `browser-use` command provides fast, persistent browser automation with sessions across commands.

## Core Workflow

1. **Navigate**: `browser-use open <url>`
2. **Inspect**: `browser-use state` — returns clickable elements with indices
3. **Interact**: `browser-use click 5`, `browser-use input 3 "text"`
4. **Verify**: `browser-use state` or `browser-use screenshot`
5. Browser stays open between commands

## Browser Modes

```bash
browser-use --browser chromium open <url>        # Default: headless Chromium
browser-use --browser chromium --headed open <url>  # Visible window
browser-use --browser real open <url>            # User's Chrome with login sessions
```

## Commands

### Navigation & State
```bash
browser-use open <url>                    # Navigate
browser-use back                          # History back
browser-use scroll down|up                # Scroll
browser-use state                         # Page elements with indices
browser-use screenshot [path.png]         # Screenshot (--full for full page)
```

### Interactions (use indices from `state`)
```bash
browser-use click <index>                 # Click element
browser-use type "text"                   # Type into focused element
browser-use input <index> "text"          # Click + type
browser-use keys "Enter"                  # Keyboard keys
browser-use select <index> "option"       # Dropdown selection
```

### Tab & Session Management
```bash
browser-use switch <tab>                  # Switch tab
browser-use close-tab [tab]               # Close tab
browser-use sessions                      # List sessions
browser-use close [--all]                 # Close session(s)
```

### JavaScript & Agent
```bash
browser-use eval "document.title"                          # Execute JS
browser-use run "Fill the contact form with test data"     # AI agent task (needs API key)
```

## Global Options

| Option | Description |
|--------|-------------|
| `--session NAME` | Named session (default: "default") |
| `--browser MODE` | chromium, real, remote |
| `--headed` | Show browser window |
| `--json` | JSON output |

## Tips

- **Always run `state` first** to see elements and indices
- **Sessions persist** — browser stays open between commands
- **Real browser mode** preserves login sessions and extensions
- CLI aliases: `bu`, `browser`, `browseruse` all work

## Cleanup

**Always close the browser when done:** `browser-use close`
