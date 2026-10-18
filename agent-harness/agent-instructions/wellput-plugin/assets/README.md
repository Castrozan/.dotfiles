# Wellput

![Live Claude Code session showing Wellput rejecting and repairing a reply](https://github.com/user-attachments/assets/8f2b00c6-ea37-486f-a118-8df32fdf0b81)

[Watch the narrated tour](https://github.com/user-attachments/assets/c1aab86a-405e-44d0-adca-d3c8d6eff208)

You are driving a bunch of high stakes agents, you are not running 100 agents, but some dozens of agents, you dont have
time to dedicate 5-15 minutes to each session by giving it your goal, asking it to create a plan and checking the plan,
the idea is to work with agents that are smart enough to take a not very well structured goal or even just a idrection,
come up with a reasonable asumption of what needs to be odne based on context, reply ot the human briefly for
clarification, another vague but more directive input fom the human is done, then work can start to be done, and each
iteration can be done with minimal interaction.

when thhis is odne a hhuman can take over multiple agents and work, instead of reading hundreds of lines of plans and
writing and validating douzens of prd's.

This is about "doing it", instead of working around it eg making plans or prds or following a orchestration guide.

when high stakes work should be done, that was never automatized, you need to make your hands dirty and launch waht i
call a "free session", no workflows, simple harness with capable tools and high inteligence for discovery and delivery
owrk.

Wellput helps you do this and maximizes you and your time. This is not for your workflows, for your automations, this is
for your daily driver high stakes, high discovery and delivery sessions.

Wellput helps people multitask. Its goal is to maximize understanding and minimize agent attention. Your agents shoudl
be as autonomous as possible and even if it needs you for smt, it should be brief, direct and make a big effort into
making you understand the work as fast and as efficient as possible.

The plugin includes a writing skill that instructs agents into what to prioritise and how to work with the hooks and
what the human needs and wants when using the system and hooks for deterministic reply validations to enforce the shape
of a good reply to the human.

## Install

Requires Python 3.12+ as `python3`. Runtime dependencies are bundled.

### Claude Code

```text
/plugin marketplace add Castrozan/wellput
/plugin install wellput@wellput
```

### Codex

```sh
codex plugin marketplace add Castrozan/wellput
codex plugin add wellput@wellput
```

Review and trust the hooks when prompted, then start a new session.

## Decisions made

`SessionStart` This is present bc it introduces agent to the system one single time and makes it clear the communication
standards needed for the session with the human from the beggining.

`Stop` This is the main worker, it enforces the shape of the system reply. We understand that in this system te human
will only read the end of turn message, which is the most important point of a agent lifetime, since is wehre humans see
the agent work and interact with the agent. When we make sure every interaciton with a session is effective and requires
minimal attention of the human, work can be paralelised, moving your attention to other high vlaue tasks and other
agents.

The default policy is:

- 100-word confirmation budget, with 10 words of grace, for short answers, tldrs, no bs direct to the core of it, short turns.
- Labels: Longer replies use **What is this session about?:**, **Done:**, and **Next:** blocks. **What is this session about?:** helps you keep track of work, it makes you never ask, "what is this session about?" in a pool of dozens of sesions, it keeps your mind and introduces you to work you forgot about. **Done:** is for this you to know what was "done" in turn, keeping you in track of te current wip. **Next:** makes it very clear what is bloking, if the owrk is finished or if a sequential job has a "next" step.
- Visuals: do you want me to draw it for you? YES! Tables, graphs, diffs, diagrams, code snippets, are all tools that clarify and discart hte need to read plain text. these have a Separate budget outside the "labels". The agent is incouraged to use the best visual cue ot help maximize human understanding with minimal reading, so choosing the best visual for the job is crucial.
- General preferences:
  - Tables need a numbered `#` column for referencing in a reply. Eg, "about #1 ...";
  - links use bare URLs or paths. Hyprlinks are cool if youre gonna use the mouse, but not that keyboard focus friendly, and bare links are clickable, soo...
  - pull or merge request references require links, bc as a multitasker you stop writing and reviewing code locally and expect all code visualization to be on your vsc. eg. pr or mr links for accessing in the browser
  - No em dashes
  - No reaction or narration openers

## Configure

Copy [wellput.json](wellput.json) to `~/.config/wellput/config.json` or `$XDG_CONFIG_HOME/wellput/config.json`.
`WELLPUT_CONFIG` selects an absolute path instead and takes precedence.

Edit budgets, labels, active checks, and feedback. Use a complete config; files do not merge. Invalid settings fail with
an error. Restart the session after editing. Without a user config, bundled defaults apply.

## License

Wellput is MIT licensed. Bundled Markdown dependencies retain their own licenses under `hooks/vendor/licenses`.
