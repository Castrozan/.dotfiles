 Problem

 1. No agents.list exists — Cleber isn't declared, so the gateway uses a fallback workspace path
 (~/.openclaw/workspace-cleber/) instead of the configured ~/openclaw/
 2. Critical secrets (gateway token, API keys) are hardcoded in openclaw.json instead of sourced from agenix
 3. Future agents need the same structural config guarantees
 4. openclaw.json is app-managed — every write (onboard, configure, doctor --fix, /config set) does a full
 JSON overwrite, destroying any $include directives or ${VAR} references

 Strategy: Post-Rebuild Explicit Patch

 On every nix rebuild, an activation script:
 1. Reads the current openclaw.json (preserving everything the app has written)
 2. Applies our pinned fields via explicit jq paths — not generic deep-merge (too risky with arrays)
 3. Injects secrets from agenix
 4. Writes back atomically via sponge

 The app can freely modify the config between rebuilds. Next rebuild re-pins our fields. No fighting.

 Why Explicit Paths (Not Deep-Merge)

 - agents.list is an array — deep-merge semantics are ambiguous (replace? concat? dedupe by id?)
 - Explicit jq paths are self-documenting and predictable
 - Adding a new pinned field = adding one jq line
 - No surprises with merge edge cases on nested objects

 New File: home/modules/openclaw/config-patch.nix

 Overlay JSON (deployed to ~/.openclaw/nix-overlay.json for debugging):

 {
   "agents": {
     "list": [
       {
         "id": "cleber",
         "default": true,
         "workspace": "/home/zanoni/openclaw"
       }
     ],
     "defaults": {
       "workspace": "/home/zanoni/openclaw"
     }
   },
   "gateway": {
     "port": 18789
   }
 }

 All values from existing config.openclaw options — no new options needed.

 Activation script (runs after writeBoundary):

 CONFIG="$HOME/.openclaw/openclaw.json"
 OVERLAY="$HOME/.openclaw/nix-overlay.json"

 # Seed if config doesn't exist
 if [ ! -f "$CONFIG" ]; then
   mkdir -p "$HOME/.openclaw"
   cp "$OVERLAY" "$CONFIG"
   exit 0
 fi

 # Backup if malformed
 if ! jq empty "$CONFIG" 2>/dev/null; then
   cp "$CONFIG" "$CONFIG.nix-backup"
   cp "$OVERLAY" "$CONFIG"
   exit 0
 fi

 # Patch: explicit paths only. App's other fields untouched.
 jq --slurpfile overlay "$OVERLAY" \
    --rawfile gwtoken /run/agenix/openclaw-gateway-token \
    --rawfile bravekey /run/agenix/brave-api-key \
    --rawfile tgtoken /run/agenix/telegram-bot-token '
   .agents.list = $overlay[0].agents.list |
   .agents.defaults.workspace = $overlay[0].agents.defaults.workspace |
   .gateway.port = $overlay[0].gateway.port |
   .gateway.auth.token = ($gwtoken | rtrimstr("\n")) |
   .tools.web.search.apiKey = ($bravekey | rtrimstr("\n"))
 ' "$CONFIG" | sponge "$CONFIG"

 What we pin vs what the app owns:
 ┌───────────────────────────┬──────────────┬────────────────────────────────────────────────────┐
 │           Field           │   Owned by   │                       Notes                        │
 ├───────────────────────────┼──────────────┼────────────────────────────────────────────────────┤
 │ agents.list               │ Nix          │ Replaced entirely on rebuild                       │
 ├───────────────────────────┼──────────────┼────────────────────────────────────────────────────┤
 │ agents.defaults.workspace │ Nix          │ Ensures fallback path is correct                   │
 ├───────────────────────────┼──────────────┼────────────────────────────────────────────────────┤
 │ gateway.port              │ Nix          │ From config.openclaw.gatewayPort                   │
 ├───────────────────────────┼──────────────┼────────────────────────────────────────────────────┤
 │ gateway.auth.token        │ Nix (agenix) │ Injected from /run/agenix/openclaw-gateway-token   │
 ├───────────────────────────┼──────────────┼────────────────────────────────────────────────────┤
 │ tools.web.search.apiKey   │ Nix (agenix) │ Injected from /run/agenix/brave-api-key            │
 ├───────────────────────────┼──────────────┼────────────────────────────────────────────────────┤
 │ Everything else           │ App          │ meta, wizard, auth, channels, hooks, logging, etc. │
 └───────────────────────────┴──────────────┴────────────────────────────────────────────────────┘
 Telegram token note:

 The Telegram token is in channels.telegram.accounts[0].token but the path depends on the channel config
 structure. The app manages channel config heavily (onboard creates it). For now, we skip pinning it — the
 app already has it. Can add later if needed.

 Modified File: home/modules/openclaw/default.nix

 Add ./config-patch.nix to imports list.

 Edge Cases
 ┌────────────────────────────────────┬───────────────────────────────────────────────────┐
 │              Scenario              │                     Behavior                      │
 ├────────────────────────────────────┼───────────────────────────────────────────────────┤
 │ Config missing (first install)     │ Seed from overlay, app fills rest on onboard      │
 ├────────────────────────────────────┼───────────────────────────────────────────────────┤
 │ Config malformed                   │ Backup to .nix-backup, seed from overlay          │
 ├────────────────────────────────────┼───────────────────────────────────────────────────┤
 │ App writes between rebuilds        │ Fine — next rebuild re-pins                       │
 ├────────────────────────────────────┼───────────────────────────────────────────────────┤
 │ App adds new top-level keys        │ Untouched                                         │
 ├────────────────────────────────────┼───────────────────────────────────────────────────┤
 │ agents.list has unexpected entries │ Replaced entirely with our list                   │
 ├────────────────────────────────────┼───────────────────────────────────────────────────┤
 │ Gateway running during patch       │ Config re-read every 200ms, picks up changes      │
 ├────────────────────────────────────┼───────────────────────────────────────────────────┤
 │ Agenix secret file missing         │ --rawfile fails → script errors, config untouched │
 └────────────────────────────────────┴───────────────────────────────────────────────────┘
 Dual Workspace Deployment

 Keep deployToBoth as safety net. Cost is negligible (symlinks). If config gets corrupted and gateway falls
 back to ~/.openclaw/workspace-{agent}/, files are still there.

 Verification

 1. cat ~/.openclaw/nix-overlay.json — expected overlay content
 2. jq '.agents.list' ~/.openclaw/openclaw.json — [{id: "cleber", default: true, workspace:
 "/home/zanoni/openclaw"}]
 3. jq '.gateway.auth.token' ~/.openclaw/openclaw.json — matches agenix secret
 4. jq '.tools.web.search.apiKey' ~/.openclaw/openclaw.json — matches agenix secret
 5. All other config keys unchanged (diff before/after)
 6. Restart gateway → send test message → Cleber responds with correct workspace context
 7. Run openclaw configure → change something → rebuild → verify pins restored

 Files

 - home/modules/openclaw/config-patch.nix — NEW
 - home/modules/openclaw/default.nix — add import