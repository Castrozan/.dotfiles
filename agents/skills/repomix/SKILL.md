---
name: repomix
description: Pack codebases into AI-friendly single files for sharing context with LLMs, generating summaries, or creating migration docs. Use when you need to analyze entire repositories or send code context to Claude.
---

# Repomix - Repository Context Packer

Repomix packs entire codebases into a single AI-optimized file with proper formatting, file structure, and token counts. Ideal for feeding large codebases to LLMs.

## Installation

```bash
# Run without installing (recommended)
npx repomix [path]

# Or install globally
npm install -g repomix
```

## Quick Start

```bash
# Pack current directory
npx repomix

# Pack specific directory
npx repomix /path/to/repo

# Pack with custom output location
npx repomix --output /tmp/packed.md

# Pack remote GitHub repo
npx repomix --remote https://github.com/user/repo
```

## Common Flags

```bash
--output <path>           # Custom output file (default: repomix-output.md)
--include <patterns>      # Include specific files/dirs (comma-separated)
--exclude <patterns>      # Exclude files/dirs (comma-separated)
--remote <url>            # Pack GitHub repo directly (no clone needed)
--style <plain|xml>       # Output format (default: xml)
--compress              # Remove comments and whitespace
```

## Output Format

Repomix generates a structured file containing:
- Repository file tree
- Token count analysis
- Security check results
- Full file contents with headers
- Top files by token count

Example structure:
```
📦 Repository Structure
├── src/
│   ├── main.py (1,234 tokens)
│   └── utils.py (567 tokens)

📊 Statistics: 554 files, 291,701 tokens

═══ File: src/main.py ═══
[file contents]
```

## Integration with OpenClaw

### With web_fetch (for GitHub repos)
```bash
# Pack a GitHub repo, then share via URL
npx repomix --remote https://github.com/user/repo --output /tmp/repo.md
# Upload to file.io or similar, then use web_fetch on the URL
```

### With browser tool
```bash
# Pack local codebase for browser-based code review
npx repomix ~/projects/myapp --output /tmp/myapp-context.md
# Use browser to navigate documentation with full context
```

### With coding agents
```bash
npx repomix /home/zanoni/.dotfiles --output /tmp/dotfiles-context.md

# In agent prompt:
# "Read /tmp/dotfiles-context.md for full codebase context, then [task]"
```

### For migration/refactoring tasks
```bash
# Before: pack current state
npx repomix --output /tmp/before-migration.md

# After: pack new state and compare
npx repomix --output /tmp/after-migration.md

# Use diff or ask Claude to analyze both files
```

## Use Cases

1. **Code Review** - Share entire codebase context with Claude for architecture review
2. **Migration Docs** - Generate comprehensive snapshots before/after major changes
3. **Onboarding** - Create AI-digestible codebase summaries for new team members
4. **Context Injection** - Feed full repo context to coding agents for better decisions
5. **Documentation** - Generate structure-aware codebase overviews

## Tips

- **Large repos**: Use `--include` to focus on relevant directories
- **Security**: Repomix auto-detects and excludes common secret files (.env, keys, etc.)
- **Token limits**: Check "Top 5 Files by Token Count" output to identify bloat
- **Binary files**: Automatically excluded (images, compiled code, etc.)
- **Config file**: Create `repomix.config.json` in repo root for persistent settings

## Example Workflows

### Analyze dotfiles before changes
```bash
npx repomix ~/.dotfiles --output /tmp/dotfiles-snapshot.md
# Make changes...
npx repomix ~/.dotfiles --output /tmp/dotfiles-after.md
# Compare or ask Claude to review changes
```

### Share project context with Claude
```bash
npx repomix ~/projects/my-app --include "src,tests" --output /tmp/app-context.md
# Upload to pastebin/gist and share URL
```

### Debug with full context
```bash
npx repomix . --exclude "node_modules,dist,build" --output /tmp/debug-context.md
# Provide to Claude: "Here's the full codebase context: [paste]"
```

## Security Notes

- Always review output before sharing externally
- Repomix detects common secret patterns but isn't foolproof
- Excluded by default: .env files, API keys, node_modules, .git, binaries
- Use `.repomixignore` (gitignore syntax) for custom exclusions

## Links

- GitHub: https://github.com/yamadashy/repomix
- Web UI: https://repomix.com
- Docs: https://github.com/yamadashy/repomix#readme
