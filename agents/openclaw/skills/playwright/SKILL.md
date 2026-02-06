# Playwright Skill

Browser automation using both Vercel's agent-browser and traditional Playwright approaches.

## Overview

This skill provides browser automation capabilities through two approaches:
1. **agent-browser** (recommended) - Vercel's AI-optimized browser CLI, faster and more context-efficient
2. **Playwright MCP** - Traditional Playwright-based automation via MCP server

## Agent-Browser (Recommended)

Vercel's agent-browser is a headless browser automation CLI specifically designed for AI agents. It's built with Rust for speed and optimized for AI context efficiency.

### Why Agent-Browser over Playwright?

- **93% less context usage** - Semantic locators instead of DOM trees
- **Faster startup** - Rust CLI boots in under 50ms
- **Compact references** - Uses refs like `@e2` instead of full accessibility dumps
- **AI-optimized output** - Accessibility tree optimized for LLM consumption
- **Session persistence** - Daemon stays running between commands

### Installation

```bash
# Via npm (recommended)
npm install -g agent-browser
agent-browser install  # Download Chromium

# On Linux, also install system dependencies
agent-browser install --with-deps
```

### Usage Pattern

```
browser open <url>          # Navigate to URL
browser snapshot            # Get accessibility tree with refs
browser click @e2           # Click by ref from snapshot
browser fill @e3 "text"     # Fill input by ref
browser get text @e1        # Get text by ref
browser screenshot          # Take screenshot
browser close               # Close browser
```

### Core Commands

| Command | Description |
|---------|-------------|
| `browser open <url>` | Navigate to URL (aliases: goto, navigate) |
| `browser click <sel>` | Click element |
| `browser fill <sel> <text>` | Clear and fill input |
| `browser type <sel> <text>` | Type into element |
| `browser press <key>` | Press key (Enter, Tab, Control+a) |
| `browser hover <sel>` | Hover over element |
| `browser scroll <dir> [px]` | Scroll up/down/left/right |
| `browser screenshot [path]` | Take screenshot |
| `browser pdf <path>` | Save as PDF |
| `browser snapshot` | Get accessibility tree with refs |
| `browser eval <js>` | Run JavaScript |
| `browser close` | Close browser |

### Find Commands (Semantic Locators)

```bash
browser find role button click --name "Submit"
browser find text "Sign In" click
browser find label "Email" fill "test@test.com"
browser find testid "login-btn" click
```

### Session Management

```bash
# Different isolated sessions
browser --session agent1 open site-a.com
browser --session agent2 open site-b.com

# Persistent profiles for auth state
browser --profile ~/.myapp-profile open myapp.com
```

## Playwright MCP Alternative

For environments where agent-browser is not available, use the Playwright MCP server approach.

### Setup

```bash
# Install Playwright MCP server
npx playwright-mcp-server

# Or add to claude_desktop_config.json:
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@anthropic-ai/playwright-mcp-server"]
    }
  }
}
```

### Direct CURL Approach

```bash
# Start the MCP server
npx @anthropic-ai/playwright-mcp-server

# Or use the skill's wrapper scripts
./openclaw/skills/playwright/scripts/browser-open.sh <url>
./openclaw/skills/playwright/scripts/browser-snapshot.sh
./openclaw/skills/playwright/scripts/browser-click.sh <selector>
```

## OpenClaw Tool Integration

OpenClaw provides native `browser` tool integration. Use this as the primary interface:

```javascript
// OpenClaw browser tool (uses agent-browser under the hood)
browser({
  action: "open",
  targetUrl: "https://example.com"
})

browser({
  action: "snapshot",
  refs: "aria"  // Get aria-refs for stable selectors
})

browser({
  action: "act",
  request: {
    kind: "click",
    ref: "e12"  // Use refs from snapshot
  }
})
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENT_BROWSER_SESSION` | Default session name |
| `AGENT_BROWSER_PROFILE` | Path to persistent profile |
| `PLAYWRIGHT_BROWSERS_PATH` | Custom browsers path |

## Examples

### Basic Login Flow

```bash
# Using agent-browser CLI
browser open https://app.example.com
browser fill @email "user@example.com"
browser fill @password "secret123"
browser click @submit
browser wait --url "**/dashboard"
browser screenshot dashboard.png
```

### Form Submission

```bash
browser open https://form.example.com
browser find label "Full Name" fill "John Doe"
browser find label "Email" fill "john@example.com"
browser find role button click --name "Submit"
browser wait --text "Thank you"
```

### Data Extraction

```bash
browser open https://quotes.example.com
SNAPSHOT=$(browser snapshot)
# Extract data using snapshot refs
browser get text @quote1
browser get text @author1
```

### Session Persistence

```bash
# First run - login and save profile
browser --profile ~/.myapp open https://app.example.com
browser fill @email "user@example.com"
browser fill @password "secret123"
browser click @login

# Subsequent runs - reuse auth
browser --profile ~/.myapp open https://app.example.com/dashboard
# Already logged in!
```

## Best Practices

1. **Prefer agent-browser** for new automations - it's faster and more AI-friendly
2. **Use refs** from snapshot instead of CSS selectors when possible
3. **Use semantic locators** (find role/label/text) for maintainable scripts
4. **Persistent profiles** for auth-heavy workflows
5. **Wait commands** before actions that trigger navigation

## References

- [Vercel agent-browser GitHub](https://github.com/vercel-labs/agent-browser)
- [Playwright MCP Server](https://github.com/anthropics/playwright-mcp-server)
- [OpenClaw Browser Tool](https://docs.openclaw.dev/tools/browser)
