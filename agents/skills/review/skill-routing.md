<skill_routing_diagnosis>
When a skill exists but the model bypasses it (uses raw tools instead), diagnose the routing chain before fixing anything.

Failure classification for routing:
- Unreachable: skill exists but description doesn't match the user's input pattern (fix description)
- Outcompeted: model sees a direct tool (WebFetch, browser MCP) and tries it before considering skills (fix with PreToolUse hook)
- Misrouted: model routes to the wrong skill (fix with eval tests + description disambiguation)
</skill_routing_diagnosis>

<diagnosis_workflow>
1. Reproduce: get the exact user input that failed routing
2. Check routing evals for existing coverage of that input pattern
3. Read the target skill's description - does it semantically match the input?
4. Check if direct tools (WebFetch, browser MCPs) would intercept before skill routing fires
5. Classify the failure, then fix
</diagnosis_workflow>

<fix_skill_description>
Update the skill's SKILL.md description AND the matching entry in the routing eval's shared system prompt. These must stay in sync. Descriptions drive all routing - embed the patterns users actually type (URLs, domain names, action verbs). Run the routing eval to verify.
</fix_skill_description>

<fix_with_pretooluse_hook>
When direct tools outcompete skills (model tries WebFetch on a URL that needs a skill), create a PreToolUse hook that blocks the tool and redirects. Look in the hooks directory for existing URL-routing hooks as a pattern. The hook receives tool input on stdin as JSON, inspects the URL, and exits 2 with a stderr redirect message.

The redirect message must be actionable: give the model the exact command or API call, not just the skill name. Skill(name) may fail in fresh sessions. Inline the minimal working command so the model can act immediately. Use wildcard matchers for MCP servers with multiple tools to avoid gaps.
</fix_with_pretooluse_hook>

<fix_with_eval_tests>
Add routing eval tests. Each test gives the shared router prompt a user input and asserts the correct skill name. Use output_not_contains to verify competing skills are NOT selected. Test bare inputs (just a URL), inputs with context ("what does this say?"), and ambiguous multi-domain inputs.
</fix_with_eval_tests>

<live_testing>
After eval tests pass, verify in a real Claude Code session. Evals test an isolated router; real sessions have competing tools, MCPs, and hooks. Use the session skill's claude capability to spawn a tmux session with the failing input as the prompt. Capture pane output to verify the model used the correct skill/tool chain. Iterate on hook messages until the model follows the redirect on first attempt.
</live_testing>
