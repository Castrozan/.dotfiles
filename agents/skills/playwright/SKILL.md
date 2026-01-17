---
name: playwright
description: Browser automation with Playwright. Use when user asks to automate web interactions, scrape websites, test web applications, fill web forms, take screenshots, or interact with dynamic web content.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<capabilities>
Navigate and interact with web pages, fill and submit forms, take screenshots, handle dynamic content (SPAs, JavaScript-heavy sites), extract data from rendered pages, automate multi-step workflows.
</capabilities>

<setup>
npm install playwright && npx playwright install chromium
</setup>

<patterns>
Basic navigation:
const { chromium } = require('playwright');
const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto('https://example.com');
await page.click('button#submit');
await page.fill('input[name="email"]', 'user@example.com');
await page.waitForSelector('.result');
await browser.close();

Screenshots: await page.screenshot({ path: 'screenshot.png', fullPage: true });

Data extraction:
const data = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('.item')).map(el => el.textContent);
});
</patterns>

<practices>
Use explicit waits (waitForSelector, waitForNavigation) over timeouts. Handle popups with page.on('popup'). Use headless: false for debugging. Capture screenshots on failure. Close browser in finally block.
</practices>

<debugging>
Run with headless: false to see browser. Use page.pause() for step-by-step. Check page.on('console') for JavaScript errors.
</debugging>
