# Humanize

Humanize helps coding agents write answers that a reader can act on without reconstructing the conversation. It preserves facts and technical terms, puts decisions first, and chooses a diff, table, diagram, or prose according to the relationship being explained.

The plugin includes the writing skill, interactive communication policy, deterministic reply validator, and reader-recovery evaluation cases extracted from [Castrozan/.dotfiles](https://github.com/Castrozan/.dotfiles). Python 3.12 or newer must be available as `python3`. The Markdown parser and its licenses are bundled; runtime hooks need no package installation, network connection, model call, Nix, or dotfiles checkout.

## Install in Claude Code

Run these commands in Claude Code:

```text
/plugin marketplace add Castrozan/humanize
/plugin install humanize@humanize
```

Start a new session after installation. The plugin registers `SessionStart` and `Stop` hooks automatically.

For a local preview, clone this repository and run `claude --plugin-dir /absolute/path/to/humanize`.

## Install in Codex

```sh
codex plugin marketplace add Castrozan/humanize
codex plugin add humanize@humanize
```

Review and trust the plugin's hook definitions when Codex requests it, then start a new session. Installation alone does not grant hook trust. See the [Codex hooks documentation](https://learn.chatgpt.com/docs/hooks).

## What runs

`SessionStart` injects the interactive policy at startup, resume, and compaction. That policy tells the agent to load the Humanize skill before substantial writing. The skill remains available for explicit requests such as “use Humanize to revise this explanation.”

`Stop` checks the final reply and requests one correction if a rule fails. It skips a reply already continued by a Stop hook, preventing an endless repair loop. Feedback identifies every violation found in that pass. Passing the checks establishes format compliance, not factual accuracy or good judgment.

The default policy uses a 100-word confirmation budget, with 10 words of grace. Longer replies use **What is this session about?:**, **Done:**, and **Next:** blocks. Separate budgets apply to the body, labels, and lists. Tables need a numbered `#` column; links use bare URLs or paths. The validator also checks unlinked pull or merge request references, sentence dashes outside quotations, and reaction or narration openers. Code, quotations, tables, diagrams, and short lists have their defined exemptions.

These are the author's complete interactive defaults. Enable the plugin in sessions where you want that response contract. It does not change tool permissions or validate generated documents.

The root `plugin.json` follows [Agent Plugins 1.0](https://agent-plugins.org/specification). Other compatible loaders can discover the skill; hook execution requires client support. Native hook registration is included for Claude Code and Codex.

## Change the reply contract

Edit `hooks/rules/reply-formats.json` in a fork. The same configuration renders the injected response format and drives validation, so changing budgets, labels, or active restrictions does not require a second policy edit. Invalid configurations fail validation instead of silently disabling enforcement.

## Verify

```sh
python3 -S tests/verify_plugin.py .
python3 -m pytest tests/test_hooks.py tests/test_human_facing_reply_rules.py tests/test_reply_format_configuration.py tests/test_reply_markdown_structure.py tests/test_reply_quotation_performance.py
claude plugin validate . --strict
```

The first command runs without site packages. The regression suite additionally needs pytest. `evals/reader_recovery.yaml` contains model-based cases from the original system; those cases are not run by structural CI, and no model-quality result is claimed for this extraction.

## Source and license

The maintained source is the Humanize skill and hooks in Castrozan/.dotfiles. Its `humanize-plugin` Nix package exports this distributable repository. To build an export from that checkout, run `nix build .#humanize-plugin`; publish the resulting directory rather than maintaining a second copy of the rules.

Humanize is MIT licensed. Bundled Markdown dependencies retain their own licenses under `hooks/vendor/licenses`.
