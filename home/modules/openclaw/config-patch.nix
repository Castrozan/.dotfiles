{
  lib,
  pkgs,
  config,
  ...
}:
let
  openclaw = config.openclaw;
  homeDir = config.home.homeDirectory;

  # Sanitize jq path ".foo.bar" → "foo_bar" for use as --arg name
  pathToArgName = path: lib.replaceStrings [ "." ] [ "_" ] (lib.removePrefix "." path);

  # Generate --arg/--argjson flags for value patches
  valueArgs = lib.concatStringsSep " " (
    lib.mapAttrsToList (
      path: val:
      let
        argName = pathToArgName path;
        json = builtins.toJSON val;
      in
      if builtins.isInt val || builtins.isBool val then
        "--argjson ${argName} '${json}'"
      else if builtins.isList val || builtins.isAttrs val then
        "--argjson ${argName} '${json}'"
      else
        "--arg ${argName} ${lib.escapeShellArg (toString val)}"
    ) openclaw.configPatches
  );

  # Generate jq filter segments for value patches
  valueFilters = lib.concatStringsSep " | " (
    lib.mapAttrsToList (
      path: _:
      let
        argName = pathToArgName path;
      in
      "${path} = $${argName}"
    ) openclaw.configPatches
  );

  # Generate --rawfile flags for secret patches
  secretArgs = lib.concatStringsSep " " (
    lib.mapAttrsToList (
      path: file:
      let
        argName = pathToArgName path;
      in
      "--rawfile ${argName} ${file}"
    ) openclaw.secretPatches
  );

  # Generate jq filter segments for secret patches
  secretFilters = lib.concatStringsSep " | " (
    lib.mapAttrsToList (
      path: _:
      let
        argName = pathToArgName path;
      in
      "${path} = ($${argName} | rtrimstr(\"\\n\"))"
    ) openclaw.secretPatches
  );

  hasValues = openclaw.configPatches != { };
  hasSecrets = openclaw.secretPatches != { };

  allArgs = lib.concatStringsSep " " (
    lib.filter (s: s != "") [
      valueArgs
      secretArgs
    ]
  );
  allFilters = lib.concatStringsSep " | " (
    lib.filter (s: s != "") [
      valueFilters
      secretFilters
    ]
  );

  # Build the overlay JSON from value patches only (secrets can't be in static files)
  overlayData = lib.mapAttrs' (
    path: val:
    let
      # Convert ".agents.list" → nested attrset path
      segments = lib.filter (s: s != "") (lib.splitString "." path);
    in
    {
      name = builtins.head segments;
      value = val;
    }
  ) openclaw.configPatches;

  jq = "${pkgs.jq}/bin/jq";
  sponge = "${pkgs.moreutils}/bin/sponge";
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

  config = lib.mkIf (hasValues || hasSecrets) {
    openclaw.configPatches = {
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

    openclaw.secretPatches = {
      ".gateway.auth.token" = "/run/agenix/openclaw-gateway-token";
      ".tools.web.search.apiKey" = "/run/agenix/brave-api-key";
    };

    # Deploy overlay JSON for debugging and seed
    home.file.".openclaw/nix-overlay.json".text = builtins.toJSON overlayData;

    # Activation script: patch openclaw.json after home-manager writes files
    home.activation.openclawConfigPatch = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
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

      ${jq} ${allArgs} '${allFilters}' "$CONFIG" | ${sponge} "$CONFIG"
    '';
  };
}
