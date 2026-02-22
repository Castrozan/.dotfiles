# Patch engine for openclaw.json — reads configPatches and secretPatches
# options, generates a jq filter + shell script, and applies them on rebuild.
#
# How it works: see config-declarations.nix for context.
# What gets patched: see config-declarations.nix for declarations.
{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;

  pathToArgName =
    path:
    lib.replaceStrings
      [
        "."
        "-"
      ]
      [
        "_"
        "_"
      ]
      (lib.removePrefix "." path);

  pathToSegments = path: lib.filter (s: s != "") (lib.splitString "." path);

  segmentNeedsQuoting = segment: builtins.match "[a-zA-Z_][a-zA-Z0-9_]*" segment == null;

  quoteJqSegment = segment: if segmentNeedsQuoting segment then ".\"${segment}\"" else ".${segment}";

  pathToJqPath = path: lib.concatStrings (map quoteJqSegment (pathToSegments path));

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
  hasDeletes = openclaw.configDeletes != [ ];

  deleteFiltersList = map (path: "del(${pathToJqPath path})") openclaw.configDeletes;

  valueFiltersList = lib.mapAttrsToList (
    path: _: "${pathToJqPath path} = $" + pathToArgName path
  ) openclaw.configPatches;

  secretFiltersList = lib.mapAttrsToList (
    path: _:
    let
      argName = pathToArgName path;
    in
    "${pathToJqPath path} = ($" + argName + " | rtrimstr(\"\\n\"))"
  ) openclaw.secretPatches;

  jqFilter = lib.concatStringsSep " | " (deleteFiltersList ++ valueFiltersList ++ secretFiltersList);

  jqFilterFile = pkgs.writeText "openclaw-patch.jq" jqFilter;

  valueArgsList = lib.mapAttrsToList (
    path: val:
    let
      argName = pathToArgName path;
      json = builtins.toJSON val;
    in
    if val == null then
      [
        "--argjson"
        argName
        "null"
      ]
    else if builtins.isInt val || builtins.isFloat val || builtins.isBool val then
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

  secretArgsList = lib.mapAttrsToList (path: file: [
    "--rawfile"
    (pathToArgName path)
    file
  ]) openclaw.secretPatches;

  allArgsList = valueArgsList ++ secretArgsList;

  patchScript = pkgs.writeShellScript "openclaw-config-patch" ''
    set -euo pipefail
    CONFIG="${homeDir}/.openclaw/openclaw.json"
    OVERLAY="${homeDir}/.openclaw/nix-overlay.json"

    export XDG_RUNTIME_DIR="''${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
    if ${pkgs.systemd}/bin/systemctl --user is-enabled agenix.service >/dev/null 2>&1; then
      ${pkgs.systemd}/bin/systemctl --user daemon-reload
      ${pkgs.systemd}/bin/systemctl --user restart agenix.service 2>/dev/null || true
    fi

    if [ ! -f "$CONFIG" ] || [ ! -s "$CONFIG" ]; then
      mkdir -p "${homeDir}/.openclaw"
      cp "$OVERLAY" "$CONFIG"
      chmod 600 "$CONFIG"
      exit 0
    fi

    if ! ${jq} empty "$CONFIG" 2>/dev/null; then
      cp "$CONFIG" "$CONFIG.nix-backup"
      cp "$OVERLAY" "$CONFIG"
      chmod 600 "$CONFIG"
      exit 0
    fi

    # Capture hash before patch
    HASH_BEFORE=$(${pkgs.coreutils}/bin/sha256sum "$CONFIG" | cut -d' ' -f1)

    # Safety: backup before patch so a jq failure can't wipe the config
    cp "$CONFIG" "$CONFIG.pre-patch"

    if ! ${jq} \
      ${
        lib.concatMapStringsSep " \\\n      " (
          args: lib.concatMapStringsSep " " lib.escapeShellArg args
        ) allArgsList
      } \
      -f ${jqFilterFile} \
      "$CONFIG" | ${sponge} "$CONFIG"; then
      echo "WARNING: openclaw config patch failed, restoring backup" >&2
      cp "$CONFIG.pre-patch" "$CONFIG"
      exit 0
    fi

    # Verify patch didn't produce empty/invalid JSON
    if [ ! -s "$CONFIG" ] || ! ${jq} empty "$CONFIG" 2>/dev/null; then
      echo "WARNING: openclaw config patch produced invalid JSON, restoring backup" >&2
      cp "$CONFIG.pre-patch" "$CONFIG"
      exit 0
    fi

    # Capture hash after patch
    HASH_AFTER=$(${pkgs.coreutils}/bin/sha256sum "$CONFIG" | cut -d' ' -f1)

    if [ "$HASH_BEFORE" != "$HASH_AFTER" ]; then
      sync
    fi
  '';
in
{
  options.openclaw = {
    configDeletes = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "jq-paths to delete from openclaw.json on every rebuild (runs before patches)";
    };

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
    home.file.".openclaw/nix-overlay.json".text = overlayJson;

    home.activation.openclawConfigPatch = lib.mkIf (hasValues || hasSecrets || hasDeletes) (
      lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${patchScript}
      ''
    );
  };
}
