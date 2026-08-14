<claude_project_directory_slug>
A Claude Code transcript lives at `~/.claude/projects/<slug>/<session-id>.jsonl` where the slug replaces every
non-alphanumeric character in the absolute cwd with a dash, not just the separators, so a dot in the username and a
leading dot on the directory both become dashes and produce a double dash. Reproduce it with
`re.sub(r"[^a-zA-Z0-9]", "-", path)`. Any
code that reconstructs this path by replacing slashes alone will silently look in a directory that does not exist.
</claude_project_directory_slug>

<anchor_every_command_to_an_absolute_path>
The Bash tool's shell cwd is not reliably the primary working directory even when the harness prints that it reset it,
and it has silently drifted to an unrelated repository between two calls in one session. An unanchored push therefore
lands on whatever remote the drifted repository has. Anchor every git command with `git -C /absolute/path`, and start
nix, build and formatter invocations with an explicit absolute `cd`. Treat an unanchored push, commit or destructive
command as a defect even when it happens to work, and when a push names a remote you did not expect, inspect that
remote's refs before reverting anything.
</anchor_every_command_to_an_absolute_path>

<claude_model_routing_and_the_split_budget>
Claude subscription plans meter a weekly budget for Opus alone plus a separate weekly budget for every other model, on
top of a shared session limit, and all of it is shared with the web and desktop clients. Running out is therefore a
routing outcome rather than a spending one: work parked on the top tier drains one budget while the other sits
untouched.
Built-in subagents compound this, since the exploration and planning subagents inherit the session model rather than
defaulting to a cheap tier, so a fan-out on a top-tier session silently runs at that tier with nothing in the interface
saying so. A user or project subagent with the same name overrides the built-in. Never assume a built-in subagent runs
cheap, and re-read the vendor's current pricing page before quoting any figure, since all of these numbers are dated.
</claude_model_routing_and_the_split_budget>

<claude_workflow_agent_calls_take_no_turn_ceiling>
A workflow `agent()` call accepts only label, phase, schema, model, effort, isolation and agent type; it silently
discards anything else, so the `maxTurns` that reads like a ceiling does nothing and the call runs until the model stops
on its own. A review pass written with `maxTurns: 8` was measured at 194 assistant turns and 95 tool calls across seven
minutes, of which twelve seconds was tool execution and the rest was serial round trips. Bound such a call through its
prompt and its pinned effort, and read the run's own transcript under `subagents/workflows/wf_*` before believing any
cap.
</claude_workflow_agent_calls_take_no_turn_ceiling>

<claude_statusline_renders_on_conversation_updates_only>
Claude Code's statusline command re-runs when a session's conversation state changes and never on a wall-clock timer, so
an idle pane keeps its last rendered line indefinitely and a wrong number there is almost always a frozen render rather
than a computation bug. Diagnose it by comparing a monotonically changing field across panes: if they disagree, the
panes are idle and no change to the statusline script can fix it, because the harness owns the render trigger.
Separately, GNU `stat` flags do not exist on darwin, so a statusline script that uses them is dead there.
</claude_statusline_renders_on_conversation_updates_only>

<claude_config_dir_roots_the_whole_tree>
Claude Code roots its entire configuration tree at `CLAUDE_CONFIG_DIR` when set, falling back to `~/.claude`: settings,
the instruction file, skills, plugins with their marketplace and installed-plugin registries, and the top-level dotfile
all relocate together. That makes an isolated launcher the clean way to load a private marketplace or plugin without
any of it touching the default installation, while the login credential stays shared through the system keychain.
</claude_config_dir_roots_the_whole_tree>

<opencode_configuration_root>
OpenCode uses `~/.config/opencode` under its own home directory and does not honor `CLAUDE_CONFIG_DIR`. Isolate an
OpenCode harness through its own configuration root instead of assuming Claude's override crosses harness boundaries.
</opencode_configuration_root>

<account_connectors_are_not_in_the_repo>
Subscription-synced account connectors are not declared anywhere in this repository and are gated by server-side
feature flags, recorded locally only as memos. There is no nix line to remove to switch them off. The one declarative
off-switch is a denied-server list in the system-level managed settings, deployed from the host module.
</account_connectors_are_not_in_the_repo>

<codex_hooks_and_launch>
Codex hooks mirror the Claude event vocabulary but differ in two ways that break a straight port: the timeout is in
seconds rather than milliseconds, and blocking works only through a deny decision returned with a zero exit, never
through a non-zero exit. Writes arrive as a patch-application tool rather than as a write tool, so a guard keyed on the
Claude write tool name never fires. The on-PATH `codex` is a wrapper that already injects model, sandbox, approval and
screen flags, so spawn it bare in a pane; re-passing any of those flags makes it exit with a duplicate-argument error.
A Codex session bridged over MCP has no interactive approval channel back to the caller, so it must never be launched
with a sandbox or approval setting weaker than full access, or every escalation it needs is auto-rejected and it
strands.
</codex_hooks_and_launch>

<claude_add_dir_skills_need_the_nested_layout>
Claude Code loads skills from `--add-dir <dir>` only at `<dir>/.claude/skills/<name>/SKILL.md`; pointing it at a skill
directory itself grants file access and loads no skill, with nothing logged. On a name collision with the machine tier
at `~/.claude/skills` the session lists the name once and keeps the machine tier's description, so an added set that
overlaps the machine tier costs no extra context and can never shadow it.
</claude_add_dir_skills_need_the_nested_layout>

<codex_skips_a_symlinked_skill_file>
Codex loads a skill whose directory is a symlink, but silently skips one whose `SKILL.md` is itself a symlink, which is
exactly what home-manager produces for a recursive file entry. Nothing is logged and a directory listing shows every
entry present, so the only reliable check is to ask the agent to list the skills it can actually load. Never mark a
skill-set file entry recursive.
</codex_skips_a_symlinked_skill_file>

<probe_an_environment_gate_past_the_packaged_wrapper>
A packaged harness binary is reached through a generated wrapper that exports every declared environment variable before
it execs, so clearing one in the calling shell and launching the harness proves nothing: the wrapper puts it back and
the probe reads as if the variable were not the gate. Probe such a gate by running the unwrapped binary, or a copy of
the wrapper with that export filtered out, and confirm the variable's absence in the running process rather than in the
shell that started it.
</probe_an_environment_gate_past_the_packaged_wrapper>
