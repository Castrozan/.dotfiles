<vault_location>
Vault path: `$OBSIDIAN_HOME`, set in the session environment. Two zones matter: `ReadItLater Inbox/` where the capture
hotkey drops saved links, and `Second Brain/` where durable knowledge is filed. Directory names carry spaces, so quote
every shell path.
</vault_location>

<capture_inbox>
The capture inbox belongs to the ril skill and its `ril` CLI, which resolves each capture's origin, turns it into a repo
change, a study entry or a filed reference, and only then marks it done. Never summarize, rate or tag a capture from
here: an annotated capture reads as worked while nothing was learned or adopted, which is exactly the failure the ril
routine replaced.
</capture_inbox>

<second_brain>
The Second Brain has its own authoritative CONTRIBUTING contract inside the vault. Read it before writing an entry
rather than recalling its structure, since it evolves.
</second_brain>

<sync>
The vault syncs on every host through a scheduled single-pass `obsidian-headless-sync` about every 5 minutes, so the app
need not be open and an edit lands within roughly that window. Linux runs it as a systemd user timer plus oneshot
service, macOS as a launchd agent on a 300 second interval. Concurrent runs contend, so a sync log complaining about
another instance is normal rather than a fault.
</sync>
