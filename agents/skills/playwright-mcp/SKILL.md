---
name: playwright-mcp
description: "Browser automation with persistent agent browser. Primary: pw CLI (~400ms/cmd). Fallback: Playwright MCP server via Claude Code MCP integration."
---

# Browser Automation

## Setup (one-time)

The agent browser uses a dedicated profile (`~/.local/share/pw-browser/`), but the user probably already set up the accounts and browser so you can use, but sometimes for **one time setups only**, you can ask the user to open the browser in headed mode. Examples:

```bash
pw open https://web.whatsapp.com --headed   # User scans QR code, then closes browser
pw open https://accounts.google.com --headed # User logs into Google, then closes browser
pw open https://github.com/login --headed    # User logs into GitHub, then closes browser
```

This auto-stops the headless browser, opens a visible window for the user to log in manually, and saves the session. Sessions persist across reboots. So no need to ask user before checking if you don't already have it all set up.

## pw CLI (Primary — ~400ms per command)

Persistent browser + Playwright library. Browser stays alive between commands.

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

| Command | Description |
|---------|-------------|
| `pw open <url> [--new] [--headed]` | Navigate (--new = new tab, --headed = visible window) |
| `pw elements` | Interactive elements with `[index]` — use with `click` |
| `pw snap` | Accessibility tree (semantic YAML) |
| `pw text` | Full page text content |
| `pw click <index\|selector>` | Click element by index or CSS selector |
| `pw click-text <text>` | Click by visible text |
| `pw fill <selector> <value>` | Fill input field |
| `pw type <selector> <value>` | Type into field (keystroke by keystroke) |
| `pw select <selector> <value>` | Select dropdown option |
| `pw press <key>` | Press keyboard key (Enter, Tab, etc.) |
| `pw screenshot [path] [--full]` | Screenshot (default: /tmp/pw-screenshot.png) |
| `pw eval <js>` | Evaluate JavaScript, print result |
| `pw html` | Full page HTML |
| `pw scroll <up\|down> [px]` | Scroll page |
| `pw back` / `pw forward` | Navigation history |
| `pw wait <selector>` | Wait for element to appear |
| `pw wait --text <text>` | Wait for text to appear |
| `pw tabs` | List open tabs |
| `pw tab <n>` | Switch to tab |
| `pw status` | Check if browser is running |
| `pw close` | Kill agent browser |

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
