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

## How it works

**The agent has the context. You shouldn’t have to rebuild it.**

Wellput assumes the end-of-turn reply may be all you read. It should make the work understandable without sending you back through the conversation.

**The skill guides the writing. The hook enforces the format.** `SessionStart` introduces the rules once; `Stop` checks the reply and requests repairs. You shouldn’t have to keep correcting how the agent communicates.

The work stays open-ended. The handoff to you doesn’t.

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

## Small rules, less friction

Numbered rows in agent tables let you reply “about #2.” Bare URLs and paths support keyboard navigation. PR and MR links take you straight to the work.

Start with substance, not reactions or narration. The default also excludes em and en dashes outside quotations, a configurable style preference.

## Configure

**No configuration needed to start.** Bundled defaults apply until you provide your own.

To change budgets, labels, checks, or repair feedback, copy `wellput.json` to `~/.config/wellput/config.json`, or `$XDG_CONFIG_HOME/wellput/config.json` when using XDG.

For a different location, set `WELLPUT_CONFIG` to an absolute path. It takes precedence over the default locations.

Use a complete config; files aren’t merged. Invalid settings produce an error. Restart the session after editing.

## License

Wellput is MIT licensed. Bundled Markdown dependencies retain their own licenses under `hooks/vendor/licenses`.
