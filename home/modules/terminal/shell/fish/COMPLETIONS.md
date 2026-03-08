# Fish Shell Enhanced Completions

This configuration enhances fish shell autocompletions with AI-powered and intelligent tools.

## Installed Tools

### Atuin (AI-powered history)
- **What**: Replaces standard shell history with intelligent, searchable SQLite database
- **Features**:
  - AI-powered suggestions based on your command patterns
  - Full-text fuzzy search across your entire history
  - Sync history across machines
  - Context-aware filtering (by directory, time, etc.)
- **Usage**:
  - Press `Ctrl+R` for fuzzy history search
  - Press `Up` for directory-filtered history
  - Commands are automatically synced every 5 minutes

### Carapace (Multi-shell completions)
- **What**: Provides intelligent completions for 500+ CLI tools
- **Features**:
  - Context-aware completions with descriptions
  - Dynamic argument generation
  - Better than standard fish completions
- **Usage**: Automatically integrates with fish tab completion

### Fish Plugins

#### Autopair
- Automatically pairs brackets, quotes, and parentheses
- Press closing character to skip over it

#### Sponge
- Removes failed commands from history
- Prevents typos from polluting your autosuggestions

#### Puffer
- Text expansion plugin
- Example: `...` expands to `../..`
- `!!` expands to previous command

#### fzf-fish (already installed)
- `Ctrl+Alt+F`: Fuzzy file search
- `Ctrl+Alt+L`: Fuzzy cd search
- `Ctrl+R`: Fuzzy history search (now enhanced by Atuin)

## Configuration Enhancements

### Autosuggestion Strategy
- Uses both `history` and `match_previous` strategies
- Suggests commands based on what you typically run in similar contexts

### Completion Styling
- Inline descriptions for faster scanning
- Color-coded completion menu
- Cyan prefix highlighting for better visibility

## Keybindings

- `Right Arrow` or `Ctrl+F`: Accept entire suggestion
- `Alt+Right` or `Alt+F`: Accept one word
- `Tab`: Show completion menu
- `Ctrl+R`: Atuin fuzzy history search
- `Up/Down`: Navigate history (filtered by current directory with Atuin)

## Performance Tips

1. **Lazy-loaded completions**: Completions are only loaded when you use the command
2. **Carapace caching**: Completions are cached for performance
3. **Atuin indexing**: History is indexed for instant fuzzy search

## Status

✓ **All plugins are now active!**

Your fish shell now has:
- Atuin 18.10.0 (AI-powered history) - already configured in `home/modules/atuin.nix`
- Carapace 1.5.5 (500+ CLI tool completions)
- Autopair (bracket/quote pairing)
- Sponge (failed command filtering)
- Puffer (text expansions)
- fzf-fish (fuzzy finding)

## Configuration Notes

**Atuin** is configured to:
- Run in **local-only mode** (no sync)
- Filter history by directory when using `Up` arrow
- Filter out common commands (`cd`, `ls`, `exit`)
- You have disabled the up-arrow override with `--disable-up-arrow` flag

If you want to enable sync across machines:
1. Edit `home/modules/atuin.nix`
2. Set `auto_sync = true` and `sync_frequency = "5m"`
3. Run `rebuild`
4. Run `atuin register` or `atuin login`
