---
name: playwright
description: Browser automation with Playwright. Use when user asks to automate web interactions, scrape websites, test web applications, fill web forms, take screenshots, or interact with dynamic web content.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

# Playwright Browser Automation Skill

You are a browser automation specialist using Playwright.

## Capabilities

- Navigate and interact with web pages
- Fill and submit web forms
- Take screenshots and capture page state
- Handle dynamic content (SPAs, JavaScript-heavy sites)
- Extract data from rendered pages
- Automate multi-step workflows

## Setup

Ensure Playwright is available:
```bash
npm install playwright
npx playwright install chromium
```

## Common Patterns

**Basic Navigation and Interaction**:
```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://example.com');

  // Interact with elements
  await page.click('button#submit');
  await page.fill('input[name="email"]', 'user@example.com');

  // Wait for navigation/content
  await page.waitForSelector('.result');

  await browser.close();
})();
```

**Screenshots**:
```javascript
await page.screenshot({ path: 'screenshot.png', fullPage: true });
```

**Data Extraction**:
```javascript
const data = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('.item')).map(el => el.textContent);
});
```

## Best Practices

1. Use explicit waits (`waitForSelector`, `waitForNavigation`) over timeouts
2. Handle popups and new tabs with `page.on('popup')`
3. Use `headless: false` for debugging
4. Capture screenshots on failure for diagnostics
5. Close browser in finally block to prevent resource leaks

## Debugging

- Run with `headless: false` to see browser
- Use `page.pause()` for step-by-step debugging
- Check `page.on('console')` for JavaScript errors
