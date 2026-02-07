---
name: playwright-mcp
description: Playwright MCP server provides AI-driven browser automation with snapshot-based control. Faster and more reliable than traditional Playwright automation due to incremental snapshot approach.
status: experimental
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<!-- TODO: Browser automation needs a definitive consolidated approach.
     Test all 3 tools (browser-use, playwright, playwright-mcp), pick the fastest/most reliable,
     consolidate into one canonical skill. Track: which works best for OpenClaw's use case
     (auth sites, form filling, scraping). -->

<capabilities>
Browser automation via MCP (Model Context Protocol) with snapshot-based state management. Navigate pages, click elements, fill forms, take screenshots, and extract data. Incremental snapshots make it faster and more reliable than traditional automation.
</capabilities>

<architecture>
Playwright MCP is an MCP server exposing browser automation through the Model Context Protocol via stdio. Key advantage: **Snapshot-based** approach takes incremental DOM snapshots instead of full page state, significantly faster for AI-driven automation.

Tools provided: page navigation (goto, goBack, goForward, reload), element interaction (click, fill, hover, select), screenshots/snapshots, JavaScript evaluation, network/console monitoring.
</architecture>

<configuration>
## MCP Server Configuration

```json
{
  "mcpServers": {
    "playwright": {
      "command": "playwright-mcp",
      "args": ["--headless", "--browser", "chromium", "--snapshot-mode", "incremental"]
    }
  }
}
```

## Key Options

- `--browser <browser>`: chrome, firefox, webkit, msedge
- `--headless`: Run headless (no visible window)
- `--device <device>`: Emulate device (e.g., "iPhone 15")
- `--snapshot-mode <mode>`: incremental, full, or none
- `--caps <caps>`: Enable vision, pdf, devtools capabilities
- `--save-trace`: Save Playwright trace for debugging
- `--user-data-dir <path>`: Persistent browser profile
- `--storage-state <path>`: Load saved auth state
</configuration>

<integration>
## OpenClaw Integration Status

**Current Status**: Installed and functional as standalone. Direct OpenClaw integration pending.

**Workarounds**:
1. Spawn playwright-mcp subprocess, communicate via stdio
2. Use traditional Playwright library (see `skills/playwright/SKILL.md`)
3. Use OpenClaw's built-in `browser` tool for simpler automation
</integration>

<practices>
- Use `--snapshot-mode incremental` for performance (default)
- Enable `--headless` for production, disable for debugging
- Save `--storage-state` to persist auth across sessions
- Use `--save-trace` for debugging failed automation
- Prefer test IDs over CSS selectors for stability
</practices>

<debugging>
## Troubleshooting

```bash
# Check installation
playwright-mcp --version && npx playwright install --dry-run chromium

# Debug: run headed with trace
playwright-mcp --headless=false --save-trace --output-dir ./debug

# View saved traces
npx playwright show-trace trace.zip
```
</debugging>

<references>
- Playwright docs: https://playwright.dev
- MCP spec: https://modelcontextprotocol.io/
- NPM: https://www.npmjs.com/package/@playwright/mcp
</references>
