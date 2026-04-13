<execution>
Run scripts/notify.sh from the session skill's notify-scripts/ subdirectory with a brief message. Voice is auto-detected from tts.json in the workspace root. Use --mobile for push notifications.
</execution>

<when_to_use>
After completing substantial work: file edits, implementations, long commands, multi-step tasks. Skip for: quick answers, explanations, back-and-forth chat.
</when_to_use>

<channels>
Desktop (default): TTS + notify-send popup. Mobile (--mobile flag): ntfy.sh push notification, bypasses DND at priority 4+.
</channels>
