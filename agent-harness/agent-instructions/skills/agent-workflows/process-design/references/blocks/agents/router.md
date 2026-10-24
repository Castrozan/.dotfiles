---
block: router
group: agents
provides: brief
needs: driver
---

# router

### What it gives

One classification of the input that dispatches it to a specialized path or agent, without taking part in the work.

### Use when

Inputs fall into distinct categories handled better separately. When the category is identifiable from the input by
code, use a deterministic dispatcher instead of a model.

### Instruction

Classify once into a closed set of routes with structured output, include a fallback route for anything unclassified,
and log every decision so misroutes can be counted.

### Pitfalls

Handoffs chained where one route was knowable upfront; an open-ended route set that grows a category per input.

### Harness

Structured-output routing in any agent SDK; code routers in Inngest AgentKit; condition nodes in visual builders.
