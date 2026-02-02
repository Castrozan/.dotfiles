# Patch engine for openclaw.json — reads configPatches and secretPatches
# options, generates a jq filter + shell script, and applies them on rebuild.
#
# How it works: see config-patch-defaults.nix for context.
# What gets patched: see config-patch-defaults.nix for declarations.
{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;

  pathToArgName = path: lib.replaceStrings [ "." ] [ "_" ] (lib.removePrefix "." path);

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

  jqFilterFile = pkgs.writeText "openclaw-patch.jq" jqFilter;

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
    home.file.".openclaw/nix-overlay.json".text = overlayJson;

    home.activation.openclawConfigPatch = lib.mkIf (hasValues || hasSecrets) (
      lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${patchScript}
      ''
    );
  };
}
