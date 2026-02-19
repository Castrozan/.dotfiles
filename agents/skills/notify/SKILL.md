---
name: notify
description: Push notifications to phone via ntfy.sh. Use when sending alerts, completion notices, error reports, or status updates to the user's mobile device.
---

<sending>
Send via curl to ntfy.sh/@notifyTopic@. Set Title header for the notification title and the message as the request body. Add Priority header (1=min, 2=low, 3=default, 4=high bypasses DND, 5=urgent until acknowledged). Add Click header for tap-to-open URL. Use Markdown: yes header for formatted messages.
</sending>

<action_buttons>
Add interactive buttons with the Actions header: "http, Label, https://url, clear=true". Multiple actions separated by semicolons.
</action_buttons>

<patterns>
On error: cmd || curl -H "Title: Error" -H "Priority: high" -d "$(hostname): cmd failed" ntfy.sh/@notifyTopic@
After long task: ./task.sh && curl -H "Title: Done" -d "Task finished at $(date)" ntfy.sh/@notifyTopic@
</patterns>

<security>
Topic is a password — anyone with it can send notifications. Never commit to public repos. Use env vars for topics in scripts.
</security>
