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

### dangerous-command-blocker.py
**Event**: PreToolUse (Bash)

Blocks or warns about potentially dangerous shell commands:
- **Blocks**: `rm -rf /`, `mkfs`, `dd of=/dev/sd`, fork bombs, piping curl/wget to shell
- **Warns**: `rm -rf`, `git push --force`, `git reset --hard`, `chmod 777`, `sudo rm`, destructive SQL

### tmux-reminder.py
**Event**: PreToolUse (Bash)

Reminds you to use tmux when running long-running commands like:
- npm/yarn/pnpm start/dev/build/test
- cargo run/build/test
- pytest, jest, vitest
- docker build/up/run
- nix-build, nixos-rebuild, home-manager switch

Suggests using the `/tmux` skill for session management.

### git-reminder.py
**Event**: PreToolUse (Bash)

Provides helpful reminders for git operations:
- Warns about unstaged changes before commits
- Warns about uncommitted changes before merge/rebase
- Notes when pushing to protected branches (main/master)
- Shows current branch context for merge/rebase operations

### sensitive-file-guard.py
**Event**: PreToolUse (Edit|Write)

Protects sensitive files:
- **Blocks**: `.ssh/*`, `.gnupg/*`, `*.pem`, `*.key`, `id_rsa`, `id_ed25519`
- **Warns**: `.env*`, `secrets.nix`, `secrets/*`, `credentials*`, files with passwords
- **Content scanning**: Detects hardcoded API keys, passwords, tokens, private keys

### context-injector.py
**Event**: UserPromptSubmit

Injects helpful context at session start:
- Git branch and status (uncommitted changes count)
- Project-specific context from `.claude/CONTEXT.md`
- Project type detection (Node.js, Rust, Nix flake, devenv)

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
