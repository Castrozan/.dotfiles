# Neovim keybind policy

Neovim keybinds on these machines stay small, known, and native-first. Agents must read this file
before suggesting, adding, or restoring any keybind, and update it whenever a binding is added or
removed on purpose.

## Baseline

The owned binding set is the one that shipped with the LazyVim migration, commit `44785605`. Its
authoritative list lives in the code: `program-configuration/lua/config/keymaps.lua` plus the
plugin `keys` specs under `program-configuration/lua/plugins/`. On top of it sit the LazyVim
distribution defaults as the curated community layer. Bindings added after that commit on request
were removed and are listed at the bottom of this file; they stay removed unless the owner names
one explicitly. The snacks explorer also disables its own `<c-p>` list action so the owned `C-p`
keeps working inside the explorer window, and that guard is part of the baseline.

`C-S-e` was restored on the owner's explicit request and is owned again. It moves focus between
the editor and the file explorer, and opens the explorer when none is open. It came back without
the persisted-width and resize machinery it originally shipped with, so `C-S-b`, `C-S-j`, and
`C-S-k` stay removed.

`C-S-Up` and `C-S-Down` were restored on the owner's explicit request and jump ten at a time
everywhere a cursor moves: ten lines in a buffer in normal, insert, and visual mode, and ten
entries inside the snacks pickers, the file explorer, and the telescope pickers. They stop at the
first and last line rather than refusing to move the way a bare `10j` does with fewer than ten
lines left. Lists no longer wrap either, because the owner asked for a hard stop at both ends:
snacks runs with `layout.cycle` off and telescope with `scroll_strategy` set to `limit`, so
single-step navigation stops at the ends too.

## Canonical references

Find how Neovim itself does a thing before proposing any mapping:

- `:help index` inside nvim: the complete catalog of built-in keys in every mode.
- `:help quickref`: the condensed tour of built-in commands and motions.
- `:help <key>` for what a specific key does natively, for example `:help C-t`.
- https://lazyvim.org/keymaps: the LazyVim default bindings active on these machines.
- https://vimdoc.neovim.io: the Neovim documentation rendered for reading outside the editor.

## Rules for adding a keybind

1. Built-ins first. If a native motion, command, or LazyVim default already does what the owner
   wants, teach that instead of mapping anything.
2. If nothing built-in exists, follow the LazyVim conventions: `<leader>` groups registered with
   descriptions, inside the namespaces documented at lazyvim.org/keymaps.
3. A custom map is the last resort, added in `lua/config/keymaps.lua` with a `desc`, in that
   file's existing style. That file is a chord table and nothing else: every entry is a single
   `map(...)` line pointing at a named function, so a handler carrying a body lives in its own
   module under `lua/config/`, the way `navigation/file_explorer.lua`, `navigation/pickers.lua`,
   `navigation/ten_line_jumping.lua`, `terminal.lua`, and `command_line_abbreviations.lua` do.
   Keep the exported name short enough that the `map(...)` call still fits on one line, because
   the module name already carries the subject. Picker-side bindings belong in that plugin's spec
   under `lua/plugins/` and call the same module, so a chord means the same thing in a buffer and
   in a list.
4. Never shadow a native Vim key. Check `:help <key>` before mapping; keys like `C-w` (window
   commands), `C-t` (tag pop), `C-b`/`C-f` (paging), `C-p`/`C-n` (completion and motion),
   `C-o`/`C-i` (jumplist), `J`/`K`, `Q`, and the `g` family carry native meaning. The baseline
   deliberately shadows a closed list (`C-p`, `C-t`, `C-b`, `C-<grave>`, `C-/`, and visual-mode
   `J`/`K`); do not grow it.
5. Never re-add a binding from the removed list on your own initiative.

## Removed bindings (do not restore unprompted)

`C-w` close buffer in normal and insert mode, `leader r` config reload, `C-p` in insert and
terminal mode, `C-Up`/`C-Down` viewport scroll, `C-Right`/`C-Left` word jumps,
`C-PageUp`/`C-PageDown` buffer cycling,
`C-S-PageUp`/`C-S-PageDown` buffer moving, `C-S-b`/`C-S-j`/`C-S-k` explorer show and resize,
explorer `C-n` create file, explorer `C-k e` folder toggle, explorer `y` path yank,
picker `C-v` clipboard paste, the `:q` and `:wq` quit-all abbreviations, the smart close-buffer
focus behavior on `leader c`, and the F12 file-path-under-cursor definition jump. Native
replacements for the common ones: `:w`, `:qa`, `C-y`/`C-e` scrolling, `w`/`b` word motion,
`:bnext`/`:bprevious` buffer cycling, `gd` plus `grn`/`grr` LSP actions, and `"+y` clipboard
yank.
