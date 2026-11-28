---
name: agent-api
description: Discover and use private APIs for web search, scraping, downloads, documents, audio and media generation, run jobs on other compute hosts, or read and set directives, through the agent-api capability gateway.
---

### Consumer boundary

Use `agent-api` for private provider capabilities. Choose from its live discovery and inspect the selected input schema;
keep provider credentials and SDKs inside adapters. A configured account does not establish free quota or an authorized
generation budget.

### Directives

A directive is the user's standing order with a fixed set of targets, such as the host that runs compute jobs. List
directives through the gateway before heavy work they govern, and change one only when the user asks.

### Compute jobs

When compute placement names another host, submit a long or heavy command as a compute job; otherwise run it as usual.
Size its memory, CPU and runtime limits in the request, because the defaults fit a small single-core job. A job
receives none of the session's environment or files, so it brings its tools itself. Follow it through status and logs,
then cancel it, because a finished job holds its unit until cancelled.

### Browser context

Use the [browser skill](../../workstation/browser/SKILL.md) when the task depends on an authenticated browser session.
