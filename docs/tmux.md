# Tmux Documentation

## Resurrect

**Save**: `prefix + Ctrl-s` | **Restore**: `prefix + Ctrl-r`

### Restore from Backup

If you overwrote your session, restore from an older backup:

```bash
cd ~/.tmux/resurrect
ln -sf tmux_resurrect_YYYYMMDDTHHMMSS.txt last
# Then: prefix + Ctrl-r
```

Backups: `~/.tmux/resurrect/` | `last` symlink points to active backup.

