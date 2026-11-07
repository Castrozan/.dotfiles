---
name: humanize
description: Use when writing for people outside a live session, like READMEs, PR or MR descriptions, handoffs, chat messages, emails, long-lived docs, bug reports, status updates, release notes. Not for live session replies.
---

### Scope

Write for a person who reads later, with no chance to ask you what you meant. Live session replies belong to `wellput`
and commit messages belong to `coding`.

### Reader first

Readers scan: they read headings first, then the body under the heading they need, and few read more than a quarter of
the words. Put the point, decision, or ask in the first line, start each heading with the words a reader scans for, and
fold detail most readers skip into a collapsed section or a link.

Write for a competent reader who lacks your context. Name the thing, the person, and the date instead of "it", "they",
or "recently", and never let a link or earlier history carry meaning the text itself omits.

### Plain style

Keep sentences near 15 to 20 words, rewrite any above 25, and never exceed 40. Keep each paragraph to one idea and at
most five sentences. Use active voice, address the reader as you, put a condition before its instruction, and write
headings in sentence case.

Cut hype, filler, and openers like "there is". Use descriptive link text, ISO dates, and units on every number. Wrong
documentation is worse than none, so state only what you verified and mark a guess as a guess.

### Representation selection

Show what prose struggles to carry, choosing the smallest useful form. Use prose for a linear answer, numbered lists for
steps, tables for comparisons and option matrices, and diffs for exact edits. Use trees for ownership, state models for
transitions, and diagrams or sequences for dependencies and failure paths. Show material actors and relationships
without repeating a visual's contents in prose or wrapping paragraphs in table rows.

Use a cropped screenshot or short recording for visual state and interactions, never an image of text, code, or terminal
output. Keep each Mermaid diagram small and split a large one. Fold logs and long output into a `<details>` block, and
use at most two alerts per document.

Give every image alt text under 155 characters that states its meaning, and never let color alone carry a status: pair a
status emoji with a word. GitHub and GitLab render Mermaid, `<details>`, and alerts; chat apps do not, so attach an
image there instead.

### Length

Start from the budget of the matching case, write the draft, then cut toward half. When content outgrows the budget,
move it into a linked document and leave a one-line summary in its place.

### Cases and examples

Read the matching case file before writing: each shows the shape, budget, visuals, and a worked example.

[README](examples/readme.md): one-line description under 120 characters, a quickstart of at most five commands, 300 to
1,500 words.

[Pull or merge request](examples/pull-request.md): imperative title under 72 characters, 50 to 300 words, and
before-and-after evidence for visible changes.

[Handoff](examples/handoff.md): 150 to 400 words for a shift and up to 800 for leave, one line per open item with an
owner and a next action.

[Chat message](examples/chat-message.md): the ask in the first line, at most 60 words for a question and 150 for an
update.

[Email](examples/email.md): action and deadline in the subject, the ask in the first line, under 150 words.

[Long-lived documentation](examples/long-lived-docs.md): one Diátaxis type per page, an ADR of one to two pages, and a
runbook entry that fits one screen.

[Bug report](examples/bug-report.md): summary under 60 characters, numbered steps, and expected against actual results.

[Status update](examples/status-update.md): status word and needed decision first, 150 to 400 words.

[Release notes](examples/release-notes.md): breaking changes first and at most 20 words per entry.
