---
name: notify
description: Notify the user that substantial work finished through a desktop text alert or optional mobile push. Skip quick answers and back-and-forth chat.
---

### Execution

Run this skill's `scripts/notify.sh` with a brief message. Use `--mobile` for an additional push notification. Desktop
delivery requests silence and preserves the user's audio settings.

### Quiet hours

Block spoken notifications every day from 17:00 inclusive until 09:00 exclusive in `America/Sao_Paulo`, including
critical alerts. Preserve text delivery throughout. Use the named timezone rather than the host's timezone or a fixed
UTC offset. An unknown clock or unavailable timezone data requires silence.

### Spoken escalation

Outside quiet hours, speech requires verified critical severity, confirmation that no steward can resolve the issue, and
confirmation that nobody is already working on it. All conditions must hold for the same issue. Missing, unknown, stale,
duplicate, or conflicting evidence requires text only; alert wording and a failing test do not establish eligibility.

The available steward status does not establish these conditions, so `notify.sh` deliberately has no speech path. Do not
substitute another speech or playback command. A future evidence-backed speech path must pass through
`prepare_spoken_notification` in `scripts/speech_policy.py` immediately before delivery; its quiet-hours and eligibility
guards precede sanitization, and a `None` result forbids speech. Never unmute or change volume to deliver an alert.
