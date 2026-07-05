<vault>
Lucas's passwords live in a hosted Bitwarden free account (bitwarden.com, castro.lucas290@gmail.com); the `bw` CLI is installed on every host and agents read and write it non-interactively. It holds his Brave browser logins plus arr-stack and service credentials, and is the sole password store now that the old `pass`/GPG store is retired.
</vault>

<session>
Mint an unlocked session before any `bw` read or write: `sess="$(bw-session)"; export BW_SESSION="$sess"`. The `bw-session` helper logs in with the API key and unlocks with the master password from agenix secrets, with no prompt, desktop app, or biometrics. Re-run it whenever `bw` reports `Vault is locked` or `not logged in`; sessions expire.
</session>

<reading>
Fetch by site name or URL: `bw get password <query>`, `bw get username <query>`, `bw get item <query>` for full JSON (`.login.username`, `.login.password`, `.login.uris`), and `bw get totp <query>` when an item carries a seed. `bw get password` fails with `More than one result found` when several items share a domain: list with `bw list items --search <term>` and pass the chosen `.id`. Run `bw sync` first if a freshly added item is missing.
</reading>

<writing>
Store a credential ad hoc by piping a filled template: `bw get template item | jq '.name="X" | .login.username="u" | .login.password="p"' | bw encode | bw create item`. Edit with `bw edit item <id>` (base64 JSON on stdin). Creates and edits sync automatically.
</writing>

<handling>
Retrieved passwords are secrets: use them inline, never echo full values into chat, logs, or committed files, and mask (first char plus length) when confirming a lookup. The master password and API key are root credentials that live only in agenix; never reproduce them elsewhere.
</handling>
