# Claude Code Hooks

Hooks are trigger-based automations that fire on specific events in Claude Code. Unlike skills, they're tied to tool calls and lifecycle events.

## What Are Hooks?

Hooks are user-defined shell commands or scripts that execute automatically at specific points in Claude Code's lifecycle. They provide **deterministic control** over Claude's behavior, enabling:

- Automatic code formatting after edits
- Command validation and blocking
- Context injection and reminders
- File protection
- Logging and auditing

Hooks run with your user privileges and can intercept, modify, or block Claude's actions.

## Hook Types

| Event | When It Fires | Can Block? | Use Cases |
|-------|---------------|------------|-----------|
| **PreToolUse** | Before tool execution | Yes (exit 2) | Validate commands, block dangerous operations, reminders |
| **PostToolUse** | After tool completes | No | Format code, log results, trigger builds |
| **UserPromptSubmit** | When you send a message | Yes | Validate input, inject context |
| **Stop** | When Claude finishes responding | Yes | Verify task completion |
| **PreCompact** | Before context compaction | No | Save state before compaction |
| **Notification** | Permission requests | No | Custom notification handlers |
| **SessionStart** | Session initialization | No | Set environment variables |
| **SessionEnd** | Session termination | No | Cleanup, save state |

## Configuration

Hooks are configured in `~/.claude/settings.json` under the `hooks` key. This is managed by home-manager in `home/modules/claude/config.nix`.

### Basic Structure

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "python3 ~/.claude/hooks/my-hook.py",
          "timeout": 5000
        }]
      }
    ]
  }
}
```

### Matcher Patterns

| Pattern | Matches |
|---------|---------|
| `"Bash"` | Exact tool name |
| `"Edit\|Write"` | Multiple tools (pipe = OR) |
| `"*"` or `""` | All tools |
| `"mcp__server__.*"` | Regex pattern |

## Installed Hooks

### dangerous-command-guard.py
**Event**: PreToolUse (Bash)

Warns about potentially dangerous shell commands:
- **Dangerous patterns**: `rm -rf /`, `mkfs`, `dd of=/dev/`, filesystem operations, force push to main/master
- **Warning patterns**: `rm -rf`, `git push --force`, `git reset --hard`, `sudo rm`, destructive operations

Provides clear warnings with context about why the command might be dangerous.

### tmux-reminder.py
**Event**: PreToolUse (Bash)

Reminds you to use tmux when running long-running commands like:
- npm/yarn/pnpm start/dev/build/test
- cargo run/build/test
- pytest, jest, vitest
- docker build/up/run
- nix-build, nixos-rebuild, home-manager switch

Shows existing tmux sessions and suggests using the `/tmux` skill for session management.

### git-reminder.py
**Event**: PreToolUse (Bash)

Provides helpful reminders for git operations:
- Warns about unstaged changes before commits
- Warns about uncommitted changes before merge/rebase
- Notes when pushing to protected branches (main/master)
- Shows current branch context for merge/rebase operations

### sensitive-file-guard.py
**Event**: PreToolUse (Edit|Write)

Warns when editing potentially sensitive files:
- **File patterns**: `.env`, `.pem/.key/.crt`, `secrets.*`, `.ssh/`, `.agenix`, `.aws/`, `.kube/config`
- **Content scanning**: Detects sensitive keywords like `password`, `api_key`, `token`, `private_key`
- **Reminders**: Suggests using git-crypt or agenix for secrets management

### nix-rebuild-reminder.py
**Event**: PostToolUse (Edit|Write)

Reminds to rebuild after editing Nix configuration files:
- Detects `.nix` files and `flake.lock` changes
- Suggests appropriate rebuild command (`nixos-rebuild` vs `home-manager switch`)
- Provides smart suggestions based on file location (system vs home configs)

### subagent-context-reminder.py
**Event**: PreToolUse (Task)

Reminds to provide full context when using Claude Code subagents:
- Triggers for context-critical subagents (Explore, Plan, nix-expert, etc.)
- Analyzes prompt quality and suggests context improvements
- Provides specific tips for different subagent types

### auto-format.py
**Event**: PostToolUse (Edit|Write)

Automatically formats files after editing based on file type:
- **Nix**: nixpkgs-fmt, alejandra, nixfmt
- **Python**: black, ruff format
- **JavaScript/TypeScript**: prettier
- **JSON/YAML**: prettier, jq
- **Shell scripts**: shfmt

Only runs if formatters are available, with graceful fallback.

## Writing Custom Hooks

### Exit Codes

| Exit Code | Meaning | Behavior |
|-----------|---------|----------|
| **0** | Success | Continue, parse JSON output |
| **2** | Blocking error | Block action, show stderr to Claude |
| **Other** | Non-blocking error | Continue, show stderr in verbose mode |

### JSON Input (via stdin)

Hooks receive JSON with context:

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript",
  "cwd": "/home/user/project",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run tests"
  }
}
```

### JSON Output

Hooks can return structured JSON for control:

```json
{
  "continue": true,
  "systemMessage": "Reminder: Consider using tmux for this"
}
```

For PreToolUse, you can also modify input or change permission decisions:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": { "command": "modified command" },
    "additionalContext": "Extra context for Claude"
  }
}
```

## Using Hooks Effectively

### Understanding Hook Behavior

Hooks provide contextual reminders and safety nets for your development workflow:

1. **Non-blocking by design**: All hooks warn but don't stop your work
2. **Context-aware**: Hooks analyze what you're doing and provide relevant suggestions
3. **Performance-optimized**: Fast execution (< 1 second) to avoid workflow interruption

### Hook Workflow Examples

**Editing sensitive files**:
```
You: Edit ~/.env
Hook: 🔒 SENSITIVE FILE: Environment file - may contain API keys and secrets
      💡 Remember to review changes before committing and consider using git-crypt or agenix
```

**Running long commands**:
```
You: npm run dev
Hook: TMUX REMINDER: This command may run for a long time. Use /tmux skill to run in a managed session.
      Existing sessions: main, dev-server
```

**Using subagents**:
```
You: @nix-expert help with flake
Hook: 🤖 SUBAGENT CONTEXT REMINDER: @nix-expert loses context between calls
      Consider including:
        • Include relevant file paths and line numbers
        • Mention your NixOS version, current config structure, and what's not working
```

**After editing Nix files**:
```
You: [Edit home/modules/claude/config.nix]
Hook: ⚙️  NIX CONFIG MODIFIED: config.nix
      Run: home-manager switch
      💡 Consider testing with --dry-run first
```

### Best Practices for Working with Hooks

1. **Pay attention to warnings**: Hooks highlight important considerations you might miss
2. **Use suggested commands**: Hook recommendations are context-aware and usually helpful
3. **Don't ignore sensitive file warnings**: Review changes carefully before committing
4. **Leverage tmux suggestions**: Long-running commands benefit from session persistence
5. **Provide context to subagents**: Follow the context reminder suggestions for better results

### Customizing Hook Behavior

If hooks are too verbose or missing patterns you need:

1. **Edit hook scripts** in `agents/hooks/`
2. **Adjust patterns** in the Python files
3. **Modify timeouts** in `config.nix`
4. **Test changes** with `echo '{"tool_input":{...}}' | python3 hook.py`

## Adding New Hooks

1. Create a Python script in `~/.dotfiles/agents/hooks/`
2. Make it executable (handled by Nix)
3. Add the hook configuration to `config.nix` in the `hooks` section
4. Run `rebuild` to apply changes

## Debugging

```bash
# Run Claude with debug output
claude --debug

# Check registered hooks
/hooks

# Verbose mode during session
# Press Ctrl+O
```

## Files

- **Hook scripts**: `~/.dotfiles/agents/hooks/`
- **Configuration**: `~/.dotfiles/home/modules/claude/config.nix`
- **Module**: `~/.dotfiles/home/modules/claude/hooks.nix`
- **Symlinked to**: `~/.claude/hooks/`

## Best Practices

1. **Keep hooks fast** - Aim for sub-second execution
2. **Fail gracefully** - Use exit 0 for warnings, exit 2 only for blocking
3. **Use specific matchers** - Avoid `"*"` unless necessary
4. **Test thoroughly** - Use `claude --debug` to verify hook execution
5. **Handle JSON errors** - Always wrap `json.load()` in try/except

## Example: Adding a Project-Specific Context File

Create `.claude/CONTEXT.md` in any project to inject project-specific reminders:

```markdown
This is a Nix flake project.
- Run `nix develop` before any development
- Use `nix build` instead of manual builds
- Database migrations are in `./migrations/`
```

The `context-injector.py` hook will automatically include this in Claude's context.
