# Claude Code Scrollback

Claude Code 2.1.89+ ships a fullscreen TUI that renders on the terminal's alternate screen and uses DEC scroll-region escapes (DECSTBM) to anchor the input box at the bottom. Both behaviors prevent streamed output from reaching the terminal's native scrollback — `tmux` copy mode, `Cmd+f`, and `less` over the pane all see only what's currently rendered. Pre-2.1.89 behavior, where every assistant message appended to scrollback like a normal CLI tool, no longer exists and is not coming back: [#21470](https://github.com/anthropics/claude-code/issues/21470) (request for a no-TUI REPL) was closed as not planned.

## What Was Tested

`CLAUDE_CODE_NO_FLICKER=0` (inline mode) plus `CLAUDE_CODE_DECSTBM=0` gives partial scrollback during a session — most of the conversation reaches tmux history, but the input-box bottom-anchoring is lost and the first ~20 lines of long streams still get overwritten by claude's startup repaint. `CLAUDE_CODE_NO_FLICKER=1` (fullscreen mode) actively wipes scrollback at end-of-stream: tmux `history_size` drops to single digits even after a 200-line generation. `CLAUDE_CODE_REPL=1`, `CLAUDE_CODE_SIMPLE=1`, `CLAUDE_CODE_DISABLE_VIRTUAL_SCROLL=1`, and `--bare` exist in the binary but do not change the rendering surface. The documented `Ctrl+O` then `[` transcript-to-scrollback dump is non-functional on 2.1.119 ([#42670](https://github.com/anthropics/claude-code/issues/42670)).

## The Three-Layer Model

Layer 1 is claude's in-app scroll, available only in fullscreen mode (`CLAUDE_CODE_NO_FLICKER=1` in `home/modules/claude/config.nix`). Mouse wheel, `PageUp`/`PageDown`, `Ctrl+Home`/`Ctrl+End` navigate the entire current conversation inside claude's render tree. This is the fast path for "scroll back to look at something in this session."

Layer 2 is tmux copy mode (`prefix [`) for selecting and copying whatever Layer 1 has currently rendered on screen. Standard tmux selection, search, and clipboard integration apply. Limited to one screenful at a time.

Layer 3 is the `prefix t` toggle, which opens a maximized side pane running the current pane's most recent session jsonl through `claude-show-session` into `less`. This is the path for "select the entire conversation," "search across the whole session," or "grab text from much earlier." The viewer uses cwd to locate the encoded project directory under `~/.claude/projects/`. Toggle pattern mirrors `prefix i` (lazygit) and `prefix b` (btop).

## Past Sessions

Tmux scrollback only ever holds the current pane's lifetime. Conversations from yesterday, from another window, or from any agent invoked via `launch-project-agent` are completely outside its reach. The session jsonl files under `~/.claude/projects/<encoded-cwd>/` are the only durable record. `claude-show-session` reads the latest one for the current cwd; `claude --resume <uuid>` reloads the conversation into a live UI. Both bypass tmux scrollback entirely.

## Tmux Configuration That Matters

`~/.config/tmux/settings.conf` ships with `set -g mouse on`, `set -g alternate-screen off`, and `set-option -ga terminal-overrides ',*:smcup@:rmcup@'`. The latter two strip alt-screen requests at the tmux layer but do not stop claude's DECSTBM escapes — that's why disabling alt-screen alone never fully restored pre-2.1.89 behavior. Mouse-on is required for Layer 1's wheel scroll to reach claude inside fullscreen mode ([fullscreen docs](https://code.claude.com/docs/en/fullscreen#use-with-tmux)).

## References

- [Issue #42670](https://github.com/anthropics/claude-code/issues/42670) — Critical UX regression, alt-screen kills scrollback (open)
- [Issue #28077](https://github.com/anthropics/claude-code/issues/28077) — Allow scrolling back to view full conversation history (open)
- [Issue #21470](https://github.com/anthropics/claude-code/issues/21470) — Disable TUI in favor of traditional REPL (closed, not planned)
- [Fullscreen rendering docs](https://code.claude.com/docs/en/fullscreen)
- [Terminal config docs](https://code.claude.com/docs/en/terminal-config)
