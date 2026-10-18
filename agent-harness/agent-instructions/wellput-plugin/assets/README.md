<!-- markdownlint-disable MD033 MD041 -->

<div align="center">

<img src="assets/logo.svg" width="96" height="96" alt="Wellput logo: a mint W inside a navy speech mark with a gold full stop">

# Wellput

**Your agents work in parallel. Your attention doesn’t.**

[![Verify Wellput](https://github.com/Castrozan/wellput/actions/workflows/verify.yml/badge.svg)](https://github.com/Castrozan/wellput/actions/workflows/verify.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-6de2c7)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-e6b76a)](#install)

</div>

<!-- markdownlint-enable MD033 MD041 -->

Wellput is a **hook and a writing skill** that make end-of-turn replies easier to **understand and act on**. Recognize the session, see what got done, know whether you’re needed, and move on without rereading the conversation.

> Built for **free sessions**: high-stakes discovery and delivery, not predefined workflows.

The point isn’t just _shorter replies_. It’s putting the effort of making work understandable **on the agent**, so you can stay across dozens of sessions without giving each one your afternoon.

![Live Claude Code session showing Wellput rejecting and repairing a reply](https://github.com/user-attachments/assets/8f2b00c6-ea37-486f-a118-8df32fdf0b81)

[Watch the narrated tour](https://github.com/user-attachments/assets/c1aab86a-405e-44d0-adca-d3c8d6eff208)

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
