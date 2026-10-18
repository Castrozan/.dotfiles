# Wellput

A few dozen agents should not require a few dozen plans to review. Wellput helps you recover each session's purpose,
result, and next step with minimal reading.

Built for **free sessions** with high stakes: capable agents discover and deliver from a direction, clarifying when
needed. A writing skill guides the explanation; hooks enforce the reply's structure.

<table>
<tr><th>Hook demo · loops automatically</th><th>Free sessions · narrated tour</th></tr>
<tr>
<td width="50%"><img src="https://github.com/user-attachments/assets/98458e2d-bb10-48cc-9932-60f50bcbedee" alt="Wellput hooks load the policy, reject a sample reply, accept its correction, and apply a custom budget" width="100%" /></td>
<td width="50%"><video src="https://github.com/user-attachments/assets/653decc1-f93b-4348-b351-c9f4d5d59cbf" controls width="100%"></video></td>
</tr>
</table>

## Install

Requires Python 3.12+ as `python3`. Runtime dependencies are bundled.

**Claude Code**

```text
/plugin marketplace add Castrozan/wellput
/plugin install wellput@wellput
```

**Codex**

```sh
codex plugin marketplace add Castrozan/wellput
codex plugin add wellput@wellput
```

Review and trust the hooks when prompted, then start a new session.

## Why the hooks

`SessionStart` introduces the contract. `Stop` catches structural violations and requests a correction, with a retry
bypass that prevents endless loops. The agent still owns factual verification.

Short replies default to **100 words + 10 grace**. Longer replies recover context through three blocks:

- **What is this session about?:** the whole session's goal.
- **Done:** this turn's result.
- **Next:** remaining work or completion.

See the [full contract](skills/wellput/references/interactive-communication.md) and [defaults](wellput.json) for all
budgets, visual exemptions, and checks.

## Configure

Copy [wellput.json](wellput.json) to `~/.config/wellput/config.json` or `$XDG_CONFIG_HOME/wellput/config.json`.
`WELLPUT_CONFIG` selects an absolute path instead and takes precedence.

Edit budgets, labels, active checks, and feedback. Use a complete config; files do not merge. Invalid settings fail with
an error. Restart the session after editing. Without a user config, bundled defaults apply.

MIT licensed. Bundled dependencies retain their licenses.
