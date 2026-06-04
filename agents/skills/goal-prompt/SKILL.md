---
name: goal-prompt
description: Author a goal prompt for an autonomous or scheduled agent - a single-line plaintext brief under 4k chars. Use when writing the prompt that drives a routine, cron agent, remote trigger, or any one-field autonomous run.
---

<what_a_goal_prompt_is>
A goal prompt is the entire brief an autonomous agent receives in one prompt field: schedulers, cron routines, remote triggers, and headless one-shots accept a single string and nothing else. The agent has no follow-up turn to ask questions, so the prompt must be self-contained - it states the goal, the context needed to act, the constraints, and what "done" looks like, all up front.
</what_a_goal_prompt_is>

<hard_output_constraints>
Output is one continuous line: no newlines, no carriage returns, no markdown, no code fences, plaintext only. Many prompt fields strip or choke on line breaks, so an embedded newline silently truncates or corrupts the brief. Keep the whole string under 4000 characters; treat that as a hard ceiling, not a target. When the draft exceeds it, cut context the agent can rediscover at runtime before cutting the goal or success criteria.
</hard_output_constraints>

<inline_structure>
Structure without line breaks: use uppercase labeled segments joined by ` · ` or `. `, and inline any sequence as `1) x 2) y 3) z`. A strong default ordering is ROLE, OBJECTIVE, CONTEXT, APPROACH, CONSTRAINTS, SUCCESS, OUTPUT - drop any segment that adds nothing for the task. Labels let the agent locate each part in a wall of text; skip them only for a trivially short goal where they would outweigh the content.
</inline_structure>

<no_assumed_outcome>
State the goal, never its answer. The prompt defines what to achieve and may direct how to go about it - method, sources to weigh, order of work - but must not presume the result, name the conclusion it expects, or load the question toward one side. An agent told the answer will rationalize toward it instead of investigating; for research, analysis, or decision goals this destroys the value. Directing approach is fine ("compare X against Y on latency and cost"); biasing outcome is not ("confirm X is faster"). Keep SUCCESS a condition the work satisfies, not a verdict the agent must reach.
</no_assumed_outcome>

<content_priorities>
OBJECTIVE states the single outcome in one imperative sentence - one goal per prompt, split unrelated goals into separate prompts. CONTEXT gives only what the agent cannot discover itself: identifiers, paths, accounts, prior decisions; never paste data the agent can fetch or read at runtime. CONSTRAINTS name real foot-guns and boundaries: what not to touch, rate limits, idempotency. SUCCESS is the observable finish condition the agent checks itself against. OUTPUT names the exact delivery channel and shape the result must take.
</content_priorities>

<evergreen_and_self_contained>
The prompt runs unattended later, possibly repeatedly, so bake in no fact that goes stale faster than the schedule: prefer "today", "the latest run", "the configured channel" over hardcoded dates, counts, or one-time values. Write for an agent with zero memory of this conversation - every referent must resolve from the prompt itself or from what the agent can look up.
</evergreen_and_self_contained>

<delivery>
Produce the finished prompt as a single fenced block so it copies cleanly, then state the character count. The fence is for copying only; the content stays one physical line, never wrapped or reflowed.
</delivery>
