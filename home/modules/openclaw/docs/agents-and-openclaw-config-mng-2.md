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
 2. Applies our pinned fields via explicit jq paths
 3. Injects secrets from agenix
 4. Writes back atomically via sponge

 The app can freely modify the config between rebuilds. Next rebuild re-pins our fields. No fighting.

 Declarative Patch Interface

 Patches are defined as nix attrsets, not hardcoded jq strings. The nix module auto-generates the jq filter
 from the attrsets.

 Two categories:

 Value patches (plain values from nix)

 configPatches = {
   ".agents.list" = builtins.toJSON [
     { id = "cleber"; default = true; workspace = "/home/zanoni/openclaw"; }
   ];
   ".agents.defaults.workspace" = "/home/zanoni/openclaw";
   ".gateway.port" = 18789;
 };

 Secret patches (read from agenix files at activation time)

 secretPatches = {
   ".gateway.auth.token" = "/run/agenix/openclaw-gateway-token";
   ".tools.web.search.apiKey" = "/run/agenix/brave-api-key";
 };

 How it works

 The nix module generates:
 1. A nix-overlay.json file with all value patches (for debugging and seed)
 2. A bash activation script where:
   - Value patches become: jq '.agents.list = $val' --argjson val '...'
   - Secret patches become: jq '.gateway.auth.token = ($secret | rtrimstr("\n"))' --rawfile secret
 /run/agenix/...

 Adding/removing a pinned field = adding/removing one line in the nix attrset. No bash editing.

 Implementation: jq filter generation

 # Value patches → jq args + filter segments
 valueArgs = lib.concatStringsSep " " (lib.mapAttrsToList (path: val:
   let argName = lib.replaceStrings ["."] ["_"] (lib.removePrefix "." path);
   in if builtins.isInt val || builtins.isBool val
      then "--argjson ${argName} '${builtins.toJSON val}'"
      else if lib.hasPrefix "[" (builtins.toJSON val) || lib.hasPrefix "{" (builtins.toJSON val)
      then "--argjson ${argName} '${val}'"
      else "--arg ${argName} '${toString val}'"
 ) patches.values);

 valueFilters = lib.concatStringsSep " | " (lib.mapAttrsToList (path: val:
   let argName = lib.replaceStrings ["."] ["_"] (lib.removePrefix "." path);
   in "${path} = $${argName}"
 ) patches.values);

 # Secret patches → --rawfile args + filter segments
 secretArgs = lib.concatStringsSep " " (lib.mapAttrsToList (path: file:
   let argName = lib.replaceStrings ["."] ["_"] (lib.removePrefix "." path);
   in "--rawfile ${argName} ${file}"
 ) patches.secrets);

 secretFilters = lib.concatStringsSep " | " (lib.mapAttrsToList (path: _:
   let argName = lib.replaceStrings ["."] ["_"] (lib.removePrefix "." path);
   in "${path} = ($${argName} | rtrimstr(\"\\n\"))"
 ) patches.secrets);

 Remove Dual Workspace Deployment

 Remove deployToBoth and gatewayWorkspacePath entirely. All modules deploy only to ~/openclaw/. Once
 agents.list sets workspace: "/home/zanoni/openclaw", the gateway reads from the correct path. If the config
 is wrong, it fails visibly instead of silently falling back.

 Files to Change

 NEW: home/modules/openclaw/config-patch.nix

 Contains:
 - options.openclaw.configPatches — value patches attrset
 - options.openclaw.secretPatches — secret file patches attrset
 - Overlay JSON generation (deployed to ~/.openclaw/nix-overlay.json)
 - Activation script with auto-generated jq filter

 Default patches set in config:

 config.openclaw.configPatches = {
   ".agents.list" = builtins.toJSON [
     {
       id = openclaw.agent;
       default = true;
       workspace = "${config.home.homeDirectory}/${openclaw.workspacePath}";
     }
   ];
   ".agents.defaults.workspace" = "${config.home.homeDirectory}/${openclaw.workspacePath}";
   ".gateway.port" = openclaw.gatewayPort;
 };

 config.openclaw.secretPatches = {
   ".gateway.auth.token" = "/run/agenix/openclaw-gateway-token";
   ".tools.web.search.apiKey" = "/run/agenix/brave-api-key";
 };

 Activation script logic:
 CONFIG="$HOME/.openclaw/openclaw.json"
 OVERLAY="$HOME/.openclaw/nix-overlay.json"

 if [ ! -f "$CONFIG" ]; then
   mkdir -p "$HOME/.openclaw"
   cp "$OVERLAY" "$CONFIG"
   exit 0
 fi

 if ! jq empty "$CONFIG" 2>/dev/null; then
   cp "$CONFIG" "$CONFIG.nix-backup"
   cp "$OVERLAY" "$CONFIG"
   exit 0
 fi

 jq <generated-args> '<generated-filter>' "$CONFIG" | sponge "$CONFIG"

 MODIFY: home/modules/openclaw/config.nix

 Remove:
 - gatewayWorkspacePath option and config
 - deployToBoth option and config

 Add:
 - deployToWorkspace — simple helper that prefixes files with workspacePath:
 deployToWorkspace = files:
   lib.mapAttrs' (name: value: {
     name = "${openclaw.workspacePath}/${name}";
     inherit value;
   }) files;

 MODIFY: home/modules/openclaw/default.nix

 Add ./config-patch.nix to imports.

 MODIFY: 6 modules — replace deployToBoth → deployToWorkspace

 All these files: change openclaw.deployToBoth to openclaw.deployToWorkspace:
 - workspace.nix
 - rules.nix
 - scripts.nix
 - skills.nix
 - tts.nix

 MODIFY: home/modules/openclaw/directories.nix

 Remove gateway workspace directory creation. Only create dirs under main workspace:
 home.activation.openclawDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
   mkdir -p "${mainWorkspace}/memory"
   mkdir -p "${mainWorkspace}/projects"
 '';

 CLEANUP: ~/.openclaw/workspace-cleber/

 After successful rebuild and gateway test, remove the stale directory.

 Edge Cases
 Scenario: Config missing (first install)
 Behavior: Seed from overlay, app fills rest on onboard
 ────────────────────────────────────────
 Scenario: Config malformed
 Behavior: Backup to .nix-backup, seed from overlay
 ────────────────────────────────────────
 Scenario: App writes between rebuilds
 Behavior: Fine — next rebuild re-pins
 ────────────────────────────────────────
 Scenario: App adds new top-level keys
 Behavior: Untouched
 ────────────────────────────────────────
 Scenario: agents.list has unexpected entries
 Behavior: Replaced entirely with our list
 ────────────────────────────────────────
 Scenario: Gateway running during patch
 Behavior: Config re-read every 200ms, picks up changes
 ────────────────────────────────────────
 Scenario: Agenix secret file missing
 Behavior: --rawfile fails → script errors, config untouched (jq piped to sponge, not in-place)
 ────────────────────────────────────────
 Scenario: Adding a new pinned field
 Behavior: Add one line to configPatches or secretPatches in nix
 ────────────────────────────────────────
 Scenario: Removing a pinned field
 Behavior: Remove one line — app regains ownership next time it writes
 Verification

 1. cat ~/.openclaw/nix-overlay.json — expected overlay content
 2. jq '.agents.list' ~/.openclaw/openclaw.json — [{id: "cleber", default: true, workspace:
 "/home/zanoni/openclaw"}]
 3. jq '.gateway.auth.token' ~/.openclaw/openclaw.json — matches agenix secret
 4. jq '.tools.web.search.apiKey' ~/.openclaw/openclaw.json — matches agenix secret
 5. All other config keys unchanged
 6. ls ~/openclaw/AGENTS.md — exists (single deployment path)
 7. ls ~/.openclaw/workspace-cleber/ — should not exist (removed)
 8. Restart gateway → send test message → Cleber responds with correct workspace
 9. Run openclaw configure → change something → rebuild → verify pins restored