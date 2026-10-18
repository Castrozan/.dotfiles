# Wellput

You have a few dozen agents working on problems that need discovery, judgment, and delivery. Spending 5-15 minutes on
every session explaining a goal, requesting a plan, and checking that plan consumes the attention you needed for the
work itself. Reading hundreds of lines and validating another PRD becomes its own job.

For that work, I use what I call a **free session**: a capable agent, a plain harness, and the tools it needs to discover
and deliver. Give it a direction, let it inspect the context and form a reasonable assumption, answer a brief
clarification when needed, and let it work. Each interaction should move the work forward with minimal supervision.

Wellput is built for those daily-driver sessions, especially when the work has high stakes and the route is still
unknown. Its goal is to maximize human understanding while minimizing the attention each agent requires. You should be
able to return to a session, recover its purpose, understand the result, and make the next decision without rereading
the conversation.

The writing skill teaches the agent what the human needs and how to choose a useful explanation or visual. Hooks
introduce the communication contract and check the final reply's structure. They support autonomous work by making its
results easier to understand; the agent's tools, judgment, and verification still determine the quality of the work.

[Watch the terminal demo](https://github.com/Castrozan/wellput/releases/download/v0.2.0/wellput-demo.mp4): real hook
output showing policy injection, a rejected reply, a corrected reply, and a configuration change.

## Install in Claude Code

Requires Python 3.12 or newer on your path as `python3`. The hooks bundle their runtime dependencies.

Run these commands in Claude Code:

```text
/plugin marketplace add Castrozan/wellput
/plugin install wellput@wellput
```

Start a new session after installing.

## Install in Codex

Requires Python 3.12 or newer on your path as `python3`.

```sh
codex plugin marketplace add Castrozan/wellput
codex plugin add wellput@wellput
```

Review and trust the plugin's hooks when prompted, then start a new session. The package follows the
[Agent Plugins specification](https://agent-plugins.org/) and includes native hook manifests for Claude Code and Codex.
Hook execution in other clients depends on their support for those events.

## Decisions made

`SessionStart` introduces the communication contract before work begins. It also restores the contract when the harness
emits that event for a resumed or compacted session.

`Stop` checks the final reply, because that is the message a multitasking human is expected to read. It returns specific
repair feedback when a rule fails. A correction turn marked `stop_hook_active` bypasses another check to prevent an
endless repair loop. Structural checks cannot establish whether an answer is true or understandable; the writing skill
provides guidance for that judgment.

Short replies have a **100-word prose budget plus 10 words of grace** and require no labels. Longer replies end with
three blocks that let you recover the session and act:

| #   | Block                            | Content                                                  | Word budget  | Purpose                                                      |
| --- | -------------------------------- | -------------------------------------------------------- | ------------ | ------------------------------------------------------------ |
| 1   | **What is this session about?:** | The whole session's subject, goal, and intended outcome. | 25 + 5 grace | Recover a session you have forgotten among dozens of others. |
| 2   | **Done:**                        | What this turn established or changed.                   | 20 + 5 grace | Identify the result without reconstructing progress updates. |
| 3   | **Next:**                        | Required remaining work, a blocker, or completion.       | 20 + 5 grace | See whether you need to act and what follows.                |

The three blocks share a **50-word budget plus 10 words of grace**. Prose above them has its own **80-word budget plus
10 words of grace**. Each budget applies independently. Labels appear once, in order, with bold names and content on
the same line, separated by blank lines.

Visuals carry relationships that prose makes expensive to read. The skill chooses a focused diff for a change, a
sequence for ordering, a table for comparison, or a diagram for another relationship. Visuals and fenced code do not
consume the prose budgets. Lists of up to three items are also exempt when they satisfy the item limits. A list may
have at most five lines; each complete item has a 20-word budget plus five words of grace. Other lists count as prose.

The remaining defaults make replies easier to reference and use:

- Tables start with a numbered `#` column, so you can answer “about #1” without quoting a row.
- Bare URLs and paths work with terminal link detection and keyboard navigation. Literal code and blockquotes keep their syntax.
- Pull and merge request references include direct links, so you can inspect the work in the browser.
- Em and en dashes outside quotations are rejected. Reaction and narration openers are also rejected.

## Change the reply contract

The bundled defaults live in [wellput.json](wellput.json). To keep your settings across plugin updates, copy that whole
file to `~/.config/wellput/config.json`, or `$XDG_CONFIG_HOME/wellput/config.json` when `XDG_CONFIG_HOME` is set. Set
`WELLPUT_CONFIG` to an absolute file path if you keep your configuration elsewhere. Settings are complete documents;
they do not merge with the defaults.

Selection order is `WELLPUT_CONFIG`, then the user config if present, then the bundled defaults. Both hooks read the
selected file. Missing explicit files, invalid JSON, and invalid settings stop policy loading or block reply completion
with an error instead of silently falling back.

For example, change `formats.confirmation` to allow 60 prose words with five words of grace:

```json
{
  "maximum_words": 60,
  "grace_words": 5
}
```

That fragment replaces only the `confirmation` object inside your complete config. It changes both the session's
instructions and the hook's word limit. Restart the session after editing settings so the agent receives the updated
instructions; Stop reads the file on every invocation.

| #   | Setting                  | What you can change                                                                                           |
| --- | ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| 1   | `formats`                | Confirmation and body budgets, label names, order, instructions, individual limits, and their combined limit. |
| 2   | `lists`                  | Line limit, item budget, grace, and the number of items exempt from prose budgets.                            |
| 3   | `syntax`                 | Label emphasis, quotation pairs, apostrophe characters, and the tree-branch pattern.                          |
| 4   | `restrictions`           | Active checks, supported patterns, and violation messages. Remove an entry to disable its check.              |
| 5   | `feedback`               | The prefix and repair instruction returned after a failed check.                                              |
| 6   | `instruction_paragraphs` | The response-shape instructions rendered for the agent, including budget and label placeholders.              |

Budget and label instructions are rendered from the configured values. If you change a prose preference or disable a
check, update any corresponding instruction too. The writing skill and the other sections of
[the interactive policy](skills/wellput/references/interactive-communication.md) remain guidance outside this JSON
contract. Configuration validates supported fields and rule names; adding a new kind of check requires code.

## License

Wellput is MIT licensed. Bundled Markdown dependencies retain their own licenses under `hooks/vendor/licenses`.
