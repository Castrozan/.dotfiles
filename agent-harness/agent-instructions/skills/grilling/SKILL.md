---
name: grilling
description: Stress-test a plan, decision, or loose idea through structured questions before acting. Use when the user says "grill me", wants rigorous pushback, or needs hidden assumptions exposed.
---

<decision-ownership>
Find facts from the available context, repository and tools; ask the user only for judgments that are theirs to make.
Give a recommended answer with every question so the trade-off is visible, but keep each decision with the user.
</decision-ownership>

<decision-tree>
Map the idea as a tree whose branches are decisions and whose edges are prerequisites. The frontier is every unsettled
decision whose prerequisites are settled. Ask the whole frontier in one numbered round, then wait; a decision that
depends on an answer still open in this round belongs to a later round. Recompute the frontier after every reply.
</decision-tree>

<pressure-test>
Challenge vague success criteria, contradictions, hidden costs, missing failure behavior and choices the user appears
to accept only because the agent proposed them. When conversation would force a guess about observable behavior, offer
the cheapest reversible prototype or probe that can supply evidence, then resume the interview from what it showed.
</pressure-test>

<completion-gate>
Finish only when the frontier is empty and the user confirms the shared understanding. Summarize the settled decisions
and remaining risks, and do not act on them unless the original request already authorized action or the user now does.
</completion-gate>
