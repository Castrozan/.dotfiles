---
name: page-composer
description: Build a web page section by section with a per-section meaning gate, not a skeleton of placeholder mock content. Use when constructing a real landing page or web UI; triggers the compose-page workflow.
---

Build a web page the way a writer builds an argument: one section at a time, content first, each section earning its place before the next exists. This is the antidote to the random-skeleton failure where a page is scaffolded all at once with dummy decks and lorem placeholders that mean nothing and relate to nothing. Run the `compose-page` workflow.

The meaning gate is the job. The workflow first fixes a meaning spine, a single thesis the page argues and an ordered set of sections each declaring its one idea and why removing it loses meaning, then builds each section in order with real final content, grounding it in the markup already built so the page accumulates rather than restarts. After every section an adversarial critic refutes any element that is filler, placeholder, off-thesis, neighborless, decorative, or an unsupported claim, forcing revision before the next section begins. Skipping the spine or weakening the gate is how the skeleton failure returns.

Pass the page subject, audience, and target action plus any output format and do-not-invent constraints through the workflow's `args`. The phases, schemas, gate criteria, and revision loop live in the co-located `compose-page.js`, the single source of truth; tune behavior there rather than restating it here, or the doc drifts from the text that drives the agents. A page this workflow built lives in `example/`.
