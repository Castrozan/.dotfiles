# notify/skill.md — ntfy.sh Push Notifications

Push notifications to your phone via ntfy.sh.

## Quick Send

```bash
# Basic message
curl -H "Title: Alert" -d "Your message here" ntfy.sh/@notifyTopic@

# With priority (1-5, default: 3)
curl -H "Title: Important" -H "Priority: high" -d "High priority alert" ntfy.sh/@notifyTopic@

# With click action
curl -H "Title: Deploy Done" -H "Click: https://github.com/Castrozan/.dotfiles/actions" -d "Build succeeded" ntfy.sh/@notifyTopic@
```

## Priority Levels

| Priority | Level    | Behavior                          |
|----------|----------|-----------------------------------|
| 1        | min      | No sound/vibration                |
| 2        | low      | No sound/vibration                |
| 3        | default  | Default notification sound        |
| 4        | high     | Bypasses DND (max once/15 min)    |
| 5        | urgent   | Urgent sound until acknowledged   |

Set with `-H "Priority: high"` or `-H "X-Priority: 4"`.

## Advanced Headers

```bash
# Action buttons
curl \
  -H "Title: Approval Needed" \
  -H "Actions: http, Approve, https://api.example.com/approve, clear=true" \
  -H "Actions: http, Decline, https://api.example.com/decline, clear=true" \
  -d "Deploy production?" \
  ntfy.sh/@notifyTopic@

# Tags/emoji
curl -H "Tags: warning" -H "Title: Warning" -d "Disk space low" ntfy.sh/@notifyTopic@

# Markdown formatting
curl -H "Markdown: yes" -d "**Bold** and *italic*" ntfy.sh/@notifyTopic@
```

## Integration Examples

### On Error
```bash
cmd || curl -H "Title: Error" -H "Priority: high" -d "$(hostname): cmd failed" ntfy.sh/@notifyTopic@
```

### After Long Task
```bash
./long-task.sh && curl -H "Title: Done" -d "Task finished at $(date)" ntfy.sh/@notifyTopic@
```

### Daily Summary (from script)
```bash
#!/bin/bash
MSG="System OK | $(df -h / | awk 'NR==2{print $5}') used | $(uptime -p)"
curl -H "Title: Daily Summary" -d "$MSG" ntfy.sh/@notifyTopic@
```

## Security

- **Topic is a password**: anyone with it can send you notifications
- Keep it random/obscured (not guessable)
- Never commit to public repos
- Use env vars for topics in scripts

## Reference

- Dashboard: https://ntfy.sh/@notifyTopic@
- Docs: https://docs.ntfy.sh/
