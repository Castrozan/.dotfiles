# Post-rebuild overlay for openclaw.json.
#
# openclaw.json is app-managed — the gateway, `openclaw configure`, and
# `doctor --fix` all do full JSON overwrites. That means inline $include
# directives or env-var references don't survive. Instead, on every nix
# rebuild an activation script:
#
#   1. Reads the current openclaw.json (preserving everything the app wrote)
#   2. Applies declarative patches via jq (agents.list, workspace, port, …)
#   3. Injects secrets from agenix (gateway token, API keys)
#   4. Writes back atomically via sponge
#
# The app can freely modify the config between rebuilds. Next rebuild
# re-pins our fields. Adding/removing a pinned field = one line in the
# configPatches or secretPatches attrset.
#
# See configPatches (plain nix values) and secretPatches (agenix file paths)
# options below for the declarative interface.
{
  lib,
  pkgs,
  config,
  ...
}:
let
  openclaw = config.openclaw;
  homeDir = config.home.homeDirectory;

  pathToArgName = path: lib.replaceStrings [ "." ] [ "_" ] (lib.removePrefix "." path);

  # Split ".foo.bar" into ["foo" "bar"] for lib.setAttrByPath
  pathToSegments = path: lib.filter (s: s != "") (lib.splitString "." path);

  # Build nested attrset from flat jq-path patches (for seed JSON)
  overlayNested = lib.foldlAttrs (
    acc: path: val:
    lib.recursiveUpdate acc (lib.setAttrByPath (pathToSegments path) val)
  ) { } openclaw.configPatches;

  overlayJson = builtins.toJSON overlayNested;

  jq = "${pkgs.jq}/bin/jq";
  sponge = "${pkgs.moreutils}/bin/sponge";

  hasValues = openclaw.configPatches != { };
  hasSecrets = openclaw.secretPatches != { };

  # Build the jq patch script as a file to avoid quoting issues in '' strings
  valueFiltersList = lib.mapAttrsToList (
    path: _: "${path} = $" + pathToArgName path
  ) openclaw.configPatches;

  secretFiltersList = lib.mapAttrsToList (
    path: _:
    let
      argName = pathToArgName path;
    in
    "${path} = ($" + argName + " | rtrimstr(\"\\n\"))"
  ) openclaw.secretPatches;

  jqFilter = lib.concatStringsSep " | " (valueFiltersList ++ secretFiltersList);

  # Write the jq filter to a file (avoids shell/nix quoting)
  jqFilterFile = pkgs.writeText "openclaw-patch.jq" jqFilter;

  # Build --argjson/--arg flags for value patches
  valueArgsList = lib.mapAttrsToList (
    path: val:
    let
      argName = pathToArgName path;
      json = builtins.toJSON val;
    in
    if builtins.isInt val || builtins.isBool val then
      [
        "--argjson"
        argName
        json
      ]
    else if builtins.isList val || builtins.isAttrs val then
      [
        "--argjson"
        argName
        json
      ]
    else
      [
        "--arg"
        argName
        (toString val)
      ]
  ) openclaw.configPatches;

  # Build --rawfile flags for secret patches
  secretArgsList = lib.mapAttrsToList (path: file: [
    "--rawfile"
    (pathToArgName path)
    file
  ]) openclaw.secretPatches;

  allArgsList = valueArgsList ++ secretArgsList;

  # Write args to a file, one per line (jq supports reading args from command line)
  # Instead, build the full jq invocation as a script
  patchScript = pkgs.writeShellScript "openclaw-config-patch" ''
    set -euo pipefail
    CONFIG="${homeDir}/.openclaw/openclaw.json"
    OVERLAY="${homeDir}/.openclaw/nix-overlay.json"

    if [ ! -f "$CONFIG" ]; then
      mkdir -p "${homeDir}/.openclaw"
      cp "$OVERLAY" "$CONFIG"
      exit 0
    fi

    if ! ${jq} empty "$CONFIG" 2>/dev/null; then
      cp "$CONFIG" "$CONFIG.nix-backup"
      cp "$OVERLAY" "$CONFIG"
      exit 0
    fi

    ${jq} \
      ${
        lib.concatMapStringsSep " \\\n      " (
          args: lib.concatMapStringsSep " " lib.escapeShellArg args
        ) allArgsList
      } \
      -f ${jqFilterFile} \
      "$CONFIG" | ${sponge} "$CONFIG"
  '';
in
{
  options.openclaw = {
    configPatches = lib.mkOption {
      type = lib.types.attrsOf lib.types.anything;
      default = { };
      description = "jq-path → value pairs to pin in openclaw.json on every rebuild";
    };

    secretPatches = lib.mkOption {
      type = lib.types.attrsOf lib.types.str;
      default = { };
      description = "jq-path → agenix file path pairs to inject into openclaw.json on every rebuild";
    };
  };

  config = {
    openclaw.configPatches = lib.mkOptionDefault {
      ".agents.list" = [
        {
          id = openclaw.agent;
          default = true;
          workspace = "${homeDir}/${openclaw.workspacePath}";
        }
      ];
      ".agents.defaults.workspace" = "${homeDir}/${openclaw.workspacePath}";
      ".gateway.port" = openclaw.gatewayPort;
    };

    openclaw.secretPatches = lib.mkOptionDefault {
      ".gateway.auth.token" = "/run/agenix/openclaw-gateway-token";
      ".tools.web.search.apiKey" = "/run/agenix/brave-api-key";
    };

    home.file.".openclaw/nix-overlay.json".text = overlayJson;

    home.activation.openclawConfigPatch = lib.mkIf (hasValues || hasSecrets) (
      lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${patchScript}
      ''
    );
  };
}
