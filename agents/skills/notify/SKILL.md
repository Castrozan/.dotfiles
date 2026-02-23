---
name: notify
description: Notify the user after completing substantial work. Use when finishing long tasks, implementations, or background operations. Plays audio and shows a desktop notification by default.
---

<execution>
Run: scripts/notify.sh "brief message"

Default sends desktop notification + TTS audio. Add --mobile to also push to phone.

scripts/notify.sh "Finished refactoring the auth module"
scripts/notify.sh "Build complete, tests passing" --mobile
</execution>

<when_to_use>
After completing substantial work: file edits, implementations, long commands, multi-step tasks.
Skip for: quick answers, explanations, back-and-forth chat.
</when_to_use>

<channels>
Desktop (default): TTS via edge-tts (en-US-GuyNeural) + notify-send popup
Mobile (--mobile flag): ntfy.sh push notification, bypasses DND at priority 4+
</channels>

<mobile>
Send directly via curl to ntfy.sh/@notifyTopic@. Set Title header for notification title, message as body. Priority: 1=min, 2=low, 3=default, 4=high (bypasses DND), 5=urgent.
</mobile>
