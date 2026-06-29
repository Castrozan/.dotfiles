---
description: Build a web page section by section with a per-section meaning gate, not a skeleton of placeholder content
argument-hint:
  [page brief, e.g. "landing page for Acme, audience CTOs, action book a demo"]
---

Build the page described in $ARGUMENTS by invoking the `compose-page` workflow (Workflow tool, name `compose-page`). Never hand-scaffold the markup yourself, which reproduces the random-skeleton-of-placeholders failure this command exists to prevent.

<invocation>
Pass the workflow an args object. `brief` is the subject, the audience, and the single action the page drives, drawn from $ARGUMENTS. `output` is the target format, defaulting to a self-contained semantic HTML5 file with one inline style block when the brief is silent. `constraints` carry design tokens, voice, length, and anything the content must not invent. The workflow throws without a `brief`, so resolve one from $ARGUMENTS or ask for it before invoking rather than passing an empty brief.
</invocation>

<after_it_returns>
The workflow returns the thesis, the section spine, the per-section gate outcomes, and the assembled `page`. Write `page` to the file the brief names, or a sensible path in the target project, and report the thesis plus which sections passed the meaning gate on which attempt so the meaning trail stays visible. Do not edit the returned markup to satisfy a requirement the gate ignores: the gate judges content meaning, not visual-spec compliance, so a missed theme or token belongs back in `constraints` on a re-invocation, not in a hand-patch that detaches the page from its proof.
</after_it_returns>

The phases, schemas, and gate criteria live in the deployed `compose-page` workflow, the single source of truth; this command only drives it.
