<purpose>
A brief is the prompt passed to the Agent or Team tool when spawning a one-off subagent. Unlike a skill or agent definition, it lives only for the lifetime of that single tool call. It must be self-contained because the spawned agent inherits no memory of the parent conversation.
</purpose>

<colleague_who_walked_in>
Write briefs for a smart colleague who just walked into the room. They have no context for what you tried, what you ruled out, or why this matters. Include: what you are trying to accomplish, what you already learned, the constraints, the form the answer should take, and the response length. Trust the agent to make judgment calls inside a well-described problem; do not micromanage with a step list when the steps depend on what the agent finds.
</colleague_who_walked_in>

<lookup_vs_investigation>
Lookups hand over the exact command or query because the answer is known and the agent just needs to execute it. Investigations hand over the question and let the agent decide steps, because prescribed steps become dead weight when the premise turns out wrong. Pick the right mode before writing the brief, and do not mix them.
</lookup_vs_investigation>

<never_delegate_understanding>
Phrases like "based on your findings, fix the bug" or "based on the research, implement it" push synthesis onto the agent instead of doing it yourself. Write briefs that prove you understood the problem: include file paths, line numbers, what specifically to change, what the test should assert. If you cannot, you are not ready to delegate; finish the analysis first.
</never_delegate_understanding>

<scope_the_deliverable>
Subagent results return as a single message that the orchestrator must summarize for the user. Cap response length explicitly ("under 200 words", "punch list, done vs missing", "filenames only"). Open-ended briefs produce token-heavy responses that the orchestrator then has to compress anyway, doubling the cost. Scope the deliverable in the brief itself.
</scope_the_deliverable>

<terse_prompts_produce_shallow_work>
Command-style prompts ("review this file", "find the bug", "check the migration") produce generic shallow work because the agent has no judgment context. Add the surrounding problem so the agent can weigh tradeoffs instead of mechanically following a narrow instruction. A brief that is too short is the most common cause of subagent output that misses the point.
</terse_prompts_produce_shallow_work>

<name_applicable_skills>
Name the skills the task depends on and tell the agent to invoke each via the Skill tool before starting.
</name_applicable_skills>
