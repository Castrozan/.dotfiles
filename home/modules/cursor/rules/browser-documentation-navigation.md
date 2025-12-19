---
description: Browser documentation navigation guidelines
alwaysApply: true
---

Browser Documentation Navigation
Use browser_navigate to documentation URLs. Wait with browser_wait_for if needed, one to two seconds. Use browser_snapshot for page structure.
Navigate using direct URLs over clicking. Use browser_take_screenshot with fullPage true for visual state. Take snapshots after navigation for interactive elements.
Package pages use package-summary.html URLs. Class pages use class.html URLs. Overview pages use index.html or root URLs. Use browser_click when direct URL navigation fails.
Take screenshots after navigation steps. Document navigation path Overview to Package to Class. Explain visible content and navigation options.
Prefer direct URL navigation over clicking. Take screenshots at key points. Use browser_wait_for for loading frames or dynamic content. Fall back to direct URLs when clicking fails.
