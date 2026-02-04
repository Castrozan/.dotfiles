---
name: playwright-mcp
description: Playwright MCP server provides AI-driven browser automation with snapshot-based control. Faster and more reliable than traditional Playwright automation due to incremental snapshot approach.
status: experimental
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<capabilities>
Browser automation via MCP (Model Context Protocol) with snapshot-based state management. Navigate pages, click elements, fill forms, take screenshots, and extract data. Supports visual mode for debugging. Incremental snapshots make it faster and more reliable than traditional automation.
</capabilities>

<setup>
# Install globally
npm install -g @playwright/mcp@latest

# Install browser binaries (if not already installed)
npx playwright install chromium

# Verify installation
playwright-mcp --version
</setup>

<architecture>
Playwright MCP is an MCP server that exposes Playwright's browser automation capabilities through the Model Context Protocol. It communicates via stdio and provides tools for:
- Page navigation (goto, goBack, goForward, reload)
- Element interaction (click, fill, hover, select)
- Screenshots and snapshots
- JavaScript evaluation
- Network and console monitoring

Key advantage: **Snapshot-based** approach takes incremental DOM snapshots instead of full page state, making it significantly faster and more reliable for AI-driven automation.
</architecture>

<configuration>
## MCP Server Configuration

For Claude Desktop or compatible MCP clients, add to configuration:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "playwright-mcp",
      "args": [
        "--headless",
        "--browser", "chromium",
        "--snapshot-mode", "incremental"
      ]
    }
  }
}
```

## Common Options

- `--browser <browser>`: chrome, firefox, webkit, msedge
- `--headless`: Run headless (no visible window)
- `--device <device>`: Emulate device (e.g., "iPhone 15")
- `--viewport-size <size>`: Set viewport (e.g., "1280x720")
- `--snapshot-mode <mode>`: incremental, full, or none
- `--caps <caps>`: Enable vision, pdf, devtools capabilities
- `--save-trace`: Save Playwright trace for debugging
- `--save-video <size>`: Record video (e.g., "800x600")
- `--user-data-dir <path>`: Persistent browser profile
- `--storage-state <path>`: Load saved auth state
</configuration>

<patterns>
## Basic Usage (via MCP Client)

The MCP server exposes tools that can be called from any MCP-compatible client:

```javascript
// Navigate to a page
await mcp.call("playwright_navigate", {
  url: "https://example.com"
});

// Click an element
await mcp.call("playwright_click", {
  selector: "button#submit"
});

// Fill a form field
await mcp.call("playwright_fill", {
  selector: "input[name='email']",
  value: "user@example.com"
});

// Take a screenshot
await mcp.call("playwright_screenshot", {
  path: "screenshot.png",
  fullPage: true
});

// Get page snapshot (incremental DOM state)
await mcp.call("playwright_snapshot");
```

## Advanced Patterns

### Persistent Session (with login state)
```bash
playwright-mcp \
  --user-data-dir ./browser-profile \
  --storage-state ./auth.json
```

### Visual Debugging
```bash
playwright-mcp \
  --headless=false \
  --caps vision \
  --save-trace
```

### Device Emulation
```bash
playwright-mcp \
  --device "iPhone 15" \
  --caps vision
```

### Recording Sessions
```bash
playwright-mcp \
  --save-video=1920x1080 \
  --save-trace \
  --output-dir ./recordings
```
</patterns>

<integration>
## OpenClaw Integration Status

**Current Status**: Playwright MCP is installed and functional as a standalone tool. Direct integration with OpenClaw's agent system is pending investigation.

**Workarounds**:
1. Use via subprocess: Spawn playwright-mcp and communicate via stdio
2. Use traditional Playwright library (see `skills/playwright/SKILL.md`)
3. Use OpenClaw's built-in `browser` tool for simpler automation

**Future Work**: 
- Investigate OpenClaw's MCP server configuration mechanism
- Create plugin/extension for native MCP server support
- Document integration with OpenClaw's agent context
</integration>

<practices>
- Use `--snapshot-mode incremental` for performance (default)
- Enable `--headless` for production, disable for debugging
- Save `--storage-state` to persist auth across sessions
- Use `--save-trace` for debugging failed automation
- Prefer test IDs over CSS selectors for stability
- Set `--timeout-action` and `--timeout-navigation` appropriately
- Use `--allowed-origins` and `--blocked-origins` for security
</practices>

<debugging>
## Troubleshooting

### Server won't start
```bash
# Check installation
playwright-mcp --version
which playwright-mcp

# Check browser binaries
npx playwright install --dry-run chromium
```

### Automation fails
```bash
# Run headed to see what's happening
playwright-mcp --headless=false

# Enable trace recording
playwright-mcp --save-trace --output-dir ./debug

# Check console logs
playwright-mcp --console-level debug
```

### Performance issues
```bash
# Use incremental snapshots (default)
playwright-mcp --snapshot-mode incremental

# Disable unnecessary features
playwright-mcp --image-responses omit --caps none
```

## Trace Viewer
```bash
# View saved traces
npx playwright show-trace trace.zip
```
</debugging>

<references>
- Official MCP announcement: https://twitter.com/playwrightweb/status/1904265499422409047
- Playwright documentation: https://playwright.dev
- MCP Protocol spec: https://modelcontextprotocol.io/
- NPM package: https://www.npmjs.com/package/@playwright/mcp
</references>

<notes>
- Playwright MCP is officially maintained by the Playwright team
- Snapshot-based approach is unique and optimized for AI automation
- Visual mode provides real-time feedback during development
- Can integrate with existing Playwright infrastructure
- MCP protocol enables cross-tool AI automation workflows
</notes>
