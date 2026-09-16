### Virtualized threads return only the visible tail

A long conversation thread on a modern chat site virtualizes its middle out of the DOM, so a one-shot query for message
nodes returns only what is near the viewport and gives no signal that anything is missing: a forty-nine message thread
came back as eleven nodes that looked like a complete short conversation. Scrolling to the top and re-querying does not
fix it either, since that swaps the head in and drops the tail. Recover the whole thread with an incremental scroll
sweep that accumulates unique nodes across steps, and sanity-check the recovered count against the thread's own
numbering or its scrollbar before trusting the read.

### Server driven uis scroll inside a container

A server-driven page can scroll inside a content element rather than the window, so window-level scrolling and
document-level height reads do nothing and lazy-loaded sections never appear. Scroll the container itself. Related traps
on such pages: a locale switch needs the hyphenated form, and a print-to-PDF path needs the full event sequence rather
than a single synthetic click.

### Authenticated sites need the real browser target

Any site behind a login can only be read through the stealth target attached to the real browser profile, because that
is what carries the session. A disposable or isolated target will render a logged-out page and the scrape will look like
a content change rather than an auth failure.
