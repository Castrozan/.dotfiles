---
name: playwright-mcp
description: "Browser automation with persistent agent browser. Primary: pw CLI (~400ms/cmd). Fallback: Playwright MCP server via Claude Code MCP integration."
---

# Browser Automation

## Setup (one-time)

The agent browser uses a dedicated profile (`~/.local/share/pw-browser/`), but the user probably already set up the accounts and browser so you can use, but sometimes for **one time setups only**, you can ask the user to open the browser in headed mode. Examples:

```bash
pw open https://web.whatsapp.com --headed   # User scans QR code
```

Sessions persist across reboots. So no need to ask user before checking if you don't already have it all set up.

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

### Performance

- Cold start (browser launch): ~1s
- Each command after: ~400ms (350ms Node.js load + 50ms CDP + operation)
- Operations themselves: 2-50ms

## Playwright MCP (Fallback only — ~200ms overhead)

Configured as Claude Code MCP server. Uses the same Playwright library but communicates via MCP protocol. Slightly slower per operation (~200ms overhead) but integrated directly into Claude Code's tool system.

Available as MCP tools: `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_fill_form`, `browser_take_screenshot`, etc.
