---
name: goal-prompt
description: Author a goal prompt for an autonomous or scheduled agent - a single-line plaintext brief under 3.5k chars. Use when writing the prompt that drives a routine, cron agent, remote trigger, or any one-field autonomous run.
---

<what_a_goal_prompt_is>
A goal prompt is the entire brief an autonomous agent receives in one prompt field: schedulers, cron routines, remote triggers, and headless one-shots take one string and nothing else. There is no follow-up turn, so it must be self-contained - it states the goal, the context needed to act, the constraints, and what "done" looks like.
</what_a_goal_prompt_is>

<hard_output_constraints>
Output is one continuous line: no newlines, no markdown, no code fences, plaintext only. Many fields choke on line breaks, so an embedded newline silently truncates the brief. Keep the string under 3500 characters as a hard ceiling; the goal field rejects anything past 4000, so 3500 leaves margin for the labels and joins. When the draft exceeds it, cut context the agent can rediscover at runtime before the goal or success criteria.
</hard_output_constraints>

<inline_structure>
Structure without line breaks: uppercase labeled segments joined by ` · ` or `. `, and inline any sequence as `1) x 2) y 3) z`. Default ordering is ROLE, OBJECTIVE, CONTEXT, APPROACH, CONSTRAINTS, SUCCESS, OUTPUT - drop any segment that adds nothing. Labels let the agent locate each part; skip them only for a trivially short goal.
</inline_structure>

<no_assumed_outcome>
State the goal, never its answer. The prompt defines what to achieve and may direct how - method, sources, order of work - but must not presume the result or load the question toward one side. An agent told the answer rationalizes toward it instead of investigating. Directing approach is fine ("compare X against Y on latency and cost"); biasing outcome is not ("confirm X is faster"). Keep SUCCESS a condition the work satisfies, not a verdict.
</no_assumed_outcome>

<content_priorities>
OBJECTIVE states the single outcome in one imperative sentence - one goal per prompt, split unrelated goals apart. CONTEXT gives only what the agent cannot discover itself: identifiers, paths, accounts, prior decisions; never paste data it can fetch at runtime. CONSTRAINTS name foot-guns: what not to touch, rate limits, idempotency. SUCCESS is the observable finish condition the agent checks itself against. OUTPUT names the delivery channel and shape.
</content_priorities>

<evergreen_and_self_contained>
The prompt runs unattended later, possibly repeatedly, so bake in no fact that goes stale faster than the schedule: prefer "today", "the latest run", "the configured channel" over hardcoded dates or one-time values. Write for an agent with zero memory of this conversation - every referent must resolve from the prompt or a runtime lookup.
</evergreen_and_self_contained>

<delivery>
Produce the finished prompt as a single fenced block so it copies cleanly, then state the character count. The content stays one physical line inside the fence.
</delivery>
