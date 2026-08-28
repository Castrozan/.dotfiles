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
the persisted-width and resize machinery it originally shipped with.

`C-S-b` shows and hides the file explorer, on the owner's explicit request, which is why it came
off the removed list. The toggle moved onto it rather than doubling: `C-b` carried it before and is
native page-back again, so the deliberately shadowed list lost an entry instead of gaining one.

`C-S-Up` and `C-S-Down` were restored on the owner's explicit request and jump seven at a time
everywhere a cursor moves: seven lines in a buffer in normal, insert, and visual mode, and seven
entries inside the snacks pickers, the file explorer, and the telescope pickers. The count was ten
before the owner asked for seven. They stop at the first and last line rather than refusing to
move the way a bare `7j` does with fewer than seven lines left. Lists no longer wrap either,
because the owner asked for a hard stop at both ends: snacks runs with `layout.cycle` off and
telescope with `scroll_strategy` set to `limit`, so single-step navigation stops at the ends too.

`C-w` was restored on the owner's explicit request and closes the current file buffer in normal and
insert mode, focusing the buffer to its right and falling back to the one on its left, and landing
on the snacks dashboard once the last file buffer goes. It is mapped `nowait` so it fires instead of
waiting for a window command key, which costs the whole native `C-w` window prefix: split, close and
zoom windows with `:vsplit`, `:split`, `:close` and `:only` instead. Insert mode loses the native
delete-word-before-cursor, which has no other native key. LazyVim's `C-h`/`C-j`/`C-k`/`C-l` window
navigation expands into `<C-w>h` with `remap` on, so it would close a buffer on every window jump;
`lua/config/lazyvim_defaults.lua` rebinds those four onto `wincmd` directly to keep them clear
of the owned chord. `leader c` keeps the plain `:bd` it was pruned to, so the focus behavior lives
on `C-w` alone.

Window width resizing moved to `C-S-j` for wider and `C-S-k` for narrower, on the owner's request,
which is why those two came off the removed list. That direction was inverted once, also on
request, so keep `j` growing the window and `k` shrinking it. It is the LazyVim `vertical resize` pair rather
than the explorer-only resize that once lived here, so it works in any vertical split and happens
to be what narrows and widens the file tree. It runs in insert mode too, on the owner's request,
which the `<cmd>` right-hand side allows without leaving insert. The LazyVim `C-Left` and
`C-Right` width defaults are deleted in `lua/config/lazyvim_defaults.lua` so the chord moved
rather than doubled.

The LazyVim `C-Up` and `C-Down` height defaults are deleted in the same place. With one window and
the global statusline, `:resize -2` has no neighbour to take rows from, so it grows `cmdheight`
instead and the statusline walks up the screen and stays there until the opposite chord walks it
back down. That is one missed shift away from the owned `C-S-Up` and `C-S-Down` seven-line jumps, so
the chord kept displacing the statusline by accident. Height resizing has no chord now; use
`:resize +2` and `:resize -2`.

Those two chords carry the viewport scroll again instead, on the owner's explicit request, which
is why it came off the removed list: `C-Up` and `C-Down` scroll the view one line onto the native
`C-y` and `C-e`, in normal, insert, and visual mode. The scroll also keeps the deleted height
resize from ever showing through the chord again. The deletion call therefore runs at the top of
`lua/config/keymaps.lua`, before the chord table: run it after the table, the way it first shipped,
and it deletes the owned scroll along with the default it was meant to strip.

`C-n` creates a file, on the owner's explicit request, which is why it came off the removed list.
In a buffer it prompts for a name and creates the file next to the file that buffer holds, falling
back to the working directory for a buffer with no file of its own, then opens it; a name with
slashes in it creates the directories it needs, and an existing file is warned about rather than
overwritten. `lua/config/file_creation.lua` carries that. Inside the explorer the same chord runs
snacks' own `explorer_add`, which creates inside the selected directory or beside the selected
file, so the plugin spec overrides the picker's `<c-n>` list action the way it already overrides
`<c-p>`. Normal mode only, so insert-mode keyword completion on `C-n` survives untouched.

`C-PageUp` and `C-PageDown` were restored on the owner's explicit request and cycle the open files
in normal and insert mode, which is why they came off the removed list. They walk the bufferline in
the order it shows on screen rather than in buffer number order, so the chord and the tabs agree,
and `buffer_closing.lua` already reads that same order when it picks what to focus next. They shadow
the native previous and next tab page motions, which `gT` and `gt` still carry unmapped. Only the
cycling came back: `C-S-PageUp` and `C-S-PageDown`, which reordered the open files, stay removed.
Inside herdr the chord is shared: herdr binds it too and hands it to the pane only while nvim runs
there, so it cycles open files in nvim and switches the herdr tab everywhere else. `prefix+pageup`
and `prefix+pagedown` switch tabs from inside nvim, and the herdr half of that split lives in this
repo's herdr module rather than here.

`C-CR` imports the symbol under the cursor and `C-.` shows what that symbol is, both on the owner's
explicit request. `lua/config/missing_imports.lua` asks the language server for the code actions at
the cursor and applies the one whose title adds an import, so it works wherever a server offers the
fix rather than only in Java. Two narrowings earn one press instead of a menu: the request carries
only the diagnostics whose range covers the cursor, so a line with two unresolved symbols offers
the one being pointed at, and titles that remove, delete, organize or add all missing imports are
rejected, so the chord neither strips an import while reaching for one nor stops to ask between the
single import and the bulk fixes. A genuinely ambiguous symbol still opens the picker, which is the
only honest answer there. `C-.` carried the generic code action menu before and carries
`vim.lsp.buf.hover` now, which is the information the owner asked for; the menu it lost still lives
on LazyVim's `leader c a`, along with the bulk import fixes. Normal mode only, like the other LSP
chords in the table.

`C-Left` and `C-Right` jump a word without ever leaving the line, on the owner's explicit request,
which is why they came off the removed list. Native `C-Left` and `C-Right` are `B` and `W`, so from
the first word of a line they land on the previous line's last WORD rather than at the line's edge,
which is the behavior the owner asked to lose. `lua/config/navigation/word_jumping.lua` keeps the
same whitespace-delimited WORD stops but bounds the search to the current line, falling back to
column one going left and to the last column going right, one past it in insert mode so typing
continues at the end. Normal, insert, and visual mode; operator-pending keeps the native motion, so
`d<C-Left>` still deletes across the line break. The LazyVim width-resize defaults on these two
chords are deleted in `lua/config/lazyvim_defaults.lua` by the call at the top of
`lua/config/keymaps.lua`, so that deletion has to keep running before the chord table.

`C-;` toggles the comment on the current line and on the visual selection, on the owner's explicit
request. It is a second spelling of the owned `C-/` rather than a replacement, because `C-/` still
reaches the editor and the owner asked only for the new chord; both expand into `gcc` and `gc`, so
the comment behavior lives in one place. `C-;` carries no native meaning, so it shadows nothing.

Completion accepts on `Tab` rather than on `Enter`, on the owner's explicit request. It is the
blink.cmp `super-tab` preset selected in `lua/plugins/blink-cmp.lua`, not a hand-written mapping, so
`Tab` accepts the selected item, falls through to snippet and AI jumps, and still indents when no
menu is open, while `Enter` goes back to opening a line. `C-y` keeps accepting too, the way LazyVim
binds it.

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
   `navigation/line_jumping.lua`, `buffer_closing.lua`, `terminal.lua`, and
   `command_line_abbreviations.lua` do.
   Keep the exported name short enough that the `map(...)` call still fits on one line, because
   the module name already carries the subject. Picker-side bindings belong in that plugin's spec
   under `lua/plugins/` and call the same module, so a chord means the same thing in a buffer and
   in a list.
4. Never shadow a native Vim key. Check `:help <key>` before mapping; keys like `C-w` (window
   commands), `C-t` (tag pop), `C-b`/`C-f` (paging), `C-p`/`C-n` (completion and motion),
   `C-o`/`C-i` (jumplist), `J`/`K`, `Q`, and the `g` family carry native meaning. The baseline
   deliberately shadows a closed list (`C-w`, `C-p`, `C-t`, `C-n` in normal mode,
   `C-PageUp` and `C-PageDown` over the tab page motions, `C-Left` and `C-Right` over the WORD
   motions they narrow to one line, `C-<grave>`, `C-/`, and visual-mode `J`/`K`); do not grow it.
   When a shadowed key is also a prefix or reachable through
   another mapping's right-hand side, hunt down the defaults that expand into it, the way the
   window navigation rebind does, or the shadow fires where nobody asked for it.
5. Never re-add a binding from the removed list on your own initiative.

## Removed bindings (do not restore unprompted)

`leader r` config reload, `C-p` in insert and terminal mode, the LazyVim `C-Up`/`C-Down` window
height resize, `C-S-PageUp`/`C-S-PageDown` buffer moving, explorer `C-k e` folder toggle,
explorer `y` path yank, picker `C-v` clipboard paste, the `:q` and `:wq` quit-all abbreviations,
the smart close-buffer focus behavior on `leader c`, which `C-w` carries instead, and the F12
file-path-under-cursor definition jump. Native replacements for the common ones: `:w`, `:qa`,
`C-y`/`C-e` scrolling, `w`/`b` word motion across lines, `gd` plus `grn`/`grr` LSP actions,
`:resize` for window height, `j` for the normal-mode `C-n` motion, and `"+y` clipboard yank.
