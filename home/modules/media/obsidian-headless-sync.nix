{
  lib,
  pkgs,
  config,
  ...
}:
let
  nodejs = pkgs.nodejs_22;
  obsidianHeadlessVersion = "0.0.5";
  npmPrefix = "$HOME/.local/share/obsidian-headless-npm";
  vaultPath = "${config.home.homeDirectory}/vault";
  secretsDirectory = "${config.home.homeDirectory}/.secrets";
  obsidianHeadlessConfigDirectory = "${config.home.homeDirectory}/.config/obsidian-headless";
  obsidianHeadlessVaultId = "2b6bae3226c07323c77d47ea9cc25a42";

  nixSystemPaths = lib.concatStringsSep ":" [
    "${nodejs}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${config.home.username}/bin"
    "${config.home.homeDirectory}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  nodeGypBuildDependencies = lib.concatStringsSep ":" [
    "${nodejs}/bin"
    "${pkgs.python3}/bin"
    "${pkgs.gnumake}/bin"
    "${pkgs.gcc}/bin"
  ];

  installObsidianHeadlessViaNpm = pkgs.writeShellScript "obsidian-headless-install" ''
    set -euo pipefail
    export PATH="${nodeGypBuildDependencies}:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"
    OB_BIN="${npmPrefix}/bin/ob"

    if [ -x "$OB_BIN" ]; then
      INSTALLED_VERSION="$("$OB_BIN" --version 2>/dev/null || echo "unknown")"
      if [ "$INSTALLED_VERSION" = "${obsidianHeadlessVersion}" ]; then
        exit 0
      fi
    fi

    ${nodejs}/bin/npm install -g "obsidian-headless@${obsidianHeadlessVersion}" \
      --prefix "${npmPrefix}" \
      --registry "https://registry.npmjs.org/"
  '';

  placeObsidianHeadlessSecrets = pkgs.writeShellScript "obsidian-headless-place-secrets" ''
    set -euo pipefail

    AUTH_TOKEN_SECRET="${secretsDirectory}/obsidian-headless-auth-token"
    SYNC_CONFIG_SECRET="${secretsDirectory}/obsidian-headless-sync-config"
    SYNC_CONFIG_DIRECTORY="${obsidianHeadlessConfigDirectory}/sync/${obsidianHeadlessVaultId}"

    mkdir -p "${obsidianHeadlessConfigDirectory}"
    mkdir -p "$SYNC_CONFIG_DIRECTORY"

    cp "$AUTH_TOKEN_SECRET" "${obsidianHeadlessConfigDirectory}/auth_token"
    chmod 600 "${obsidianHeadlessConfigDirectory}/auth_token"

    cp "$SYNC_CONFIG_SECRET" "$SYNC_CONFIG_DIRECTORY/config.json"
    ${pkgs.gnused}/bin/sed -i 's|"vaultPath": "[^"]*"|"vaultPath": "${vaultPath}"|' "$SYNC_CONFIG_DIRECTORY/config.json"
    chmod 600 "$SYNC_CONFIG_DIRECTORY/config.json"
  '';

  obsidianHeadlessWrapper = pkgs.writeShellScriptBin "ob" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"
    exec "${npmPrefix}/bin/ob" "$@"
  '';

  obsidianHeadlessSyncScript = pkgs.writeShellScript "obsidian-headless-sync" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"

    OB_BIN="${npmPrefix}/bin/ob"
    if [ ! -x "$OB_BIN" ]; then
      echo "obsidian-headless not installed. Run 'ob --version' to trigger install." >&2
      exit 1
    fi

    exec "$OB_BIN" sync --continuous --path "${vaultPath}"
  '';
in
{
  home = {
    packages = [
      obsidianHeadlessWrapper
    ];

    activation.installObsidianHeadlessViaNpm = config.lib.dag.entryAfter [ "writeBoundary" ] ''
      run ${installObsidianHeadlessViaNpm}
    '';

    activation.placeObsidianHeadlessSecrets =
      config.lib.dag.entryAfter
        [
          "writeBoundary"
          "agenix"
        ]
        ''
          run ${placeObsidianHeadlessSecrets}
        '';
  };

  systemd.user.services.obsidian-headless-sync = {
    Unit = {
      Description = "Obsidian Headless Sync (continuous, bidirectional)";
      After = [ "network-online.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${obsidianHeadlessSyncScript}";
      Restart = "always";
      RestartSec = "30s";
      Environment = [
        "PATH=${nixSystemPaths}"
        "NODE_ENV=production"
      ];
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };
}
