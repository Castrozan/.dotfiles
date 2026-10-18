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

## How it works

**The skill guides the writing. The hook enforces the format.**

`SessionStart` introduces the communication rules once. `Stop` checks the end-of-turn reply and asks the agent to repair it when it breaks them.

The work stays open-ended. The reply has to be usable.

## What you come back to

**A quick answer shouldn’t become a report.** Short replies get 100 prose words, plus 10 words of grace. No required labels.

**Longer replies should bring you back into the session, not make you reconstruct it.** They end with three blocks:

| #   | Block                            | What it tells you                                              |
| --- | -------------------------------- | -------------------------------------------------------------- |
| 1   | **What is this session about?:** | The session’s goal, not just the latest step.                  |
| 2   | **Done:**                        | What this turn changed or established.                         |
| 3   | **Next:**                        | What remains, what’s blocked, or whether the work is finished. |

**Sometimes the clearest paragraph is a diff.** Tables, diagrams, graphs, and code should replace prose when they make the work easier to understand. Visuals and fenced code don’t count toward the prose budget.

**Small details make the next interaction easier.**

- Number table rows so you can reply “about #2” instead of quoting the whole thing.
- Use bare URLs and paths for keyboard-friendly navigation. Link referenced PRs and MRs so you don’t have to find them.
- Start with the answer, not a reaction or a narration of what the agent is about to do.
- No em or en dashes outside quotations.

## Configure

**No configuration needed to start.** Bundled defaults apply until you provide your own.

To change budgets, labels, checks, or repair feedback, copy `wellput.json` to `~/.config/wellput/config.json`, or `$XDG_CONFIG_HOME/wellput/config.json` when using XDG.

For a different location, set `WELLPUT_CONFIG` to an absolute path. It takes precedence over the default locations.

Use a complete config; files aren’t merged. Invalid settings produce an error. Restart the session after editing.

## License

Wellput is MIT licensed. Bundled Markdown dependencies retain their own licenses under `hooks/vendor/licenses`.
