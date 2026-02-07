---
name: playwright-mcp
description: "Playwright MCP server provides AI-driven browser automation with snapshot-based control. Faster and more reliable than traditional Playwright automation due to incremental snapshot approach."
---

# Browser Automation (Playwright MCP)

The canonical browser automation tool for OpenClaw. Uses Playwright's MCP server with snapshot-based DOM interaction.

## Core Workflow

1. **Navigate**: `browser_navigate` to URL
2. **Snapshot**: `browser_snapshot` — returns YAML DOM tree with `ref=` IDs
3. **Interact**: `browser_click ref=e6`, `browser_type ref=e5 text="..."`, `browser_fill_form`
4. **Verify**: `browser_snapshot` again or `browser_take_screenshot`
5. **Close**: `browser_close` when done

## Snapshot Format

Snapshots return an accessible YAML tree. Each interactive element has a `ref=` ID:

```yaml
- heading "Example Domain" [level=1] [ref=e3]
- paragraph [ref=e4]: Some text here.
- paragraph [ref=e5]:
  - link "Learn more" [ref=e6] [cursor=pointer]:
    - /url: https://example.com/more
- textbox "Email:" [ref=e7]
- button "Submit" [ref=e8]
```

Use the `ref` value when calling `browser_click`, `browser_type`, etc.

## Available Tools

| Tool | Description |
|------|-------------|
| `browser_navigate` | Navigate to URL |
| `browser_navigate_back` | Go back in history |
| `browser_snapshot` | DOM tree with ref IDs (use for actions) |
| `browser_take_screenshot` | Visual screenshot (can't act on it) |
| `browser_click` | Click element by ref |
| `browser_type` | Type into element by ref |
| `browser_fill_form` | Fill multiple form fields at once |
| `browser_select_option` | Select dropdown option |
| `browser_hover` | Hover over element |
| `browser_drag` | Drag and drop between elements |
| `browser_press_key` | Press keyboard key |
| `browser_file_upload` | Upload files |
| `browser_evaluate` | Execute JavaScript |
| `browser_run_code` | Run Playwright code snippet |
| `browser_tabs` | List, create, close, or select tabs |
| `browser_wait_for` | Wait for text/condition |
| `browser_handle_dialog` | Handle alert/confirm/prompt |
| `browser_console_messages` | Get console output |
| `browser_network_requests` | Get network requests |
| `browser_resize` | Resize viewport |
| `browser_close` | Close the page |

## NixOS Notes

On NixOS, system Chrome is at a non-standard path. The MCP server is configured with `--executable-path` pointing to `google-chrome-stable` from the system profile. This is handled by the MCP config in `home/modules/claude/mcp.nix`.

## Debugging

- Run headed (remove `--headless`) to see the browser
- Use `--save-trace` to capture Playwright traces
- Use `browser_console_messages` and `browser_network_requests` for debugging
- If browser not found: check `--executable-path` in MCP config
