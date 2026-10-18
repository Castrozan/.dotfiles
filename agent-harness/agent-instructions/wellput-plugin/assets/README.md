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

![Live Claude Code session showing Wellput rejecting and repairing a reply](https://raw.githubusercontent.com/Castrozan/wellput/a4a21aff55e2cf4cdd36c76d2e9cf248538f52e3/wellput-fluid-demo.gif)

[Watch the narrated tour](https://github.com/user-attachments/assets/70519b32-bcfe-4e2d-b427-6a866af8dd38)

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

## How it works

**The agent has the context. You shouldn’t have to rebuild it.**

Wellput assumes the end-of-turn reply may be all you read. It should make the work understandable without sending you back through the conversation.

**The skill guides the writing. The hook enforces the format.** `SessionStart` introduces the rules once; `Stop` checks the reply and requests repairs.

## The reply format

**Short answers stay short.** Up to 100 prose words, plus 10 words of grace, without required labels. A confirmation shouldn’t become a report.

**Longer replies bring you back into the session.** Three closing blocks answer the questions you ask when switching agents:

| #   | Block                            | Why it exists                                                             |
| --- | -------------------------------- | ------------------------------------------------------------------------- |
| 1   | **What is this session about?:** | Restore the session’s subject and goal, not just the latest step.         |
| 2   | **Done:**                        | Show what actually changed or was established, not what was planned.      |
| 3   | **Next:**                        | Make clear what remains, what’s blocked, or whether the work is finished. |

Consistent order and bold labels make answers easy to find. Separate word budgets keep the explanation from swallowing the summary.

**Sometimes the clearest paragraph is a diff.** Use tables, diagrams, and code when they save the reader work. Visuals and fenced code don’t count toward the prose budget. The goal is understanding, not just fewer words.

### Other rules

- Number table rows so you can reply “about #2.”
- Use bare URLs and paths for keyboard navigation.
- Include links when mentioning PRs or MRs.
- Start with the answer. Skip reactions and narration.
- No em or en dashes outside quotes (configurable).

## Configure

Wellput uses bundled defaults. To change budgets, labels, checks, or repair feedback:

- Copy `wellput.json` to `~/.config/wellput/config.json`.
- With XDG, use `$XDG_CONFIG_HOME/wellput/config.json`.
- For another location, set `WELLPUT_CONFIG` to an absolute path. It overrides the default locations.

## License

Wellput is MIT licensed. Bundled Markdown dependencies retain their own licenses under `hooks/vendor/licenses`.
