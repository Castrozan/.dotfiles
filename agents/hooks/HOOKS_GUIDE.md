# Claude Code Hooks - Quick Start Guide

Based on your request to understand and use hooks for better development workflow.

## What Are Hooks?

**Hooks are automatic reminders and safety checks that trigger during your Claude Code sessions.**

Think of them as a smart assistant that:
- Reminds you about tmux when running long commands
- Warns about dangerous operations before you run them
- Suggests rebuild commands after editing Nix files
- Checks for sensitive data in files you're editing
- Provides context tips when using subagents

## How They Work

Hooks fire automatically on specific events:

| When | What Happens | Example |
|------|--------------|---------|
| Before running bash commands | Safety checks, tmux reminders | `npm run dev` → "Consider tmux for session persistence" |
| Before editing files | Sensitive file warnings | Edit `.env` → "May contain API keys and secrets" |
| After editing files | Format code, rebuild reminders | Edit `.nix` → "Run: home-manager switch" |
| Using subagents | Context reminders | `@nix-expert` → "Provide NixOS version and config details" |

## Your Current Hooks

Your dotfiles are configured with these practical hooks:

### Development Workflow
- **tmux-reminder**: Suggests tmux for long-running commands
- **auto-format**: Formats code after editing (nix, python, js, etc.)
- **nix-rebuild-reminder**: Reminds to rebuild after nix file changes

### Safety & Security
- **dangerous-command-guard**: Warns about risky shell commands
- **sensitive-file-guard**: Warns when editing files with secrets
- **git-reminder**: Provides git operation context

### Productivity
- **subagent-context-reminder**: Tips for better subagent interactions

## Real Examples

**Before this system:**
```
You: rm -rf ./old-project/
Claude: [Executes command]
Result: Accidentally deleted wrong directory
```

**With hooks:**
```
You: rm -rf ./old-project/
Hook: ⚠️ WARNING: Recursive force delete - double-check the path
Claude: [Still executes, but you're warned]
```

**Development workflow improvement:**
```
You: [Edit flake.nix]
Hook: ⚙️ NIX CONFIG MODIFIED: flake.nix
      Run: nixos-rebuild switch
      💡 Consider testing with --dry-run first

You: @nix-expert help with this error
Hook: 🤖 SUBAGENT CONTEXT REMINDER: @nix-expert loses context between calls
      Consider including:
        • Your NixOS version, current config structure, and what's not working
```

## Key Benefits

1. **Fewer mistakes**: Warnings prevent common errors
2. **Better habits**: Encourages good practices (tmux, proper git workflow)
3. **Faster iterations**: Auto-formatting and rebuild reminders
4. **Context awareness**: Helps you provide better info to subagents
5. **Security**: Catches potential secret leaks before commits

## How to Use

**Nothing to learn** - hooks work automatically! Just pay attention to the messages:

- 🔒 **Sensitive file warnings** → Review carefully before committing
- ⚠️ **Command warnings** → Double-check what you're doing
- 💡 **Suggestions** → Follow the recommendations
- 🤖 **Subagent tips** → Provide the suggested context

## Customization

To modify hook behavior:

1. **Edit scripts**: `~/.dotfiles/agents/hooks/*.py`
2. **Adjust config**: `~/.dotfiles/home/modules/claude/config.nix`
3. **Apply changes**: Run `rebuild`

## Files Overview

```
~/.dotfiles/agents/hooks/          # Hook scripts
├── dangerous-command-guard.py     # Safety warnings
├── sensitive-file-guard.py        # File security
├── tmux-reminder.py               # Session management
├── git-reminder.py                # Git context
├── nix-rebuild-reminder.py        # Rebuild suggestions
├── subagent-context-reminder.py   # Better subagent use
└── auto-format.py                 # Code formatting

~/.dotfiles/home/modules/claude/   # Configuration
├── config.nix                     # Hook registrations
└── hooks.nix                      # Symlink management
```

## Quick Reference

| I want to... | Hook that helps |
|---------------|-----------------|
| Run long commands safely | `tmux-reminder.py` |
| Avoid dangerous commands | `dangerous-command-guard.py` |
| Protect sensitive files | `sensitive-file-guard.py` |
| Remember to rebuild after nix changes | `nix-rebuild-reminder.py` |
| Get better subagent responses | `subagent-context-reminder.py` |
| Keep code formatted | `auto-format.py` |
| Better git workflow | `git-reminder.py` |

Hooks make Claude Code smarter and safer without getting in your way. They're your development workflow's safety net and productivity booster combined.