{
  lib,
  pkgs,
  config,
  ...
}:
let
  nodejs = pkgs.nodejs_22;
  obsidianHeadlessVersion = "0.0.5";
  npmPrefixDirectory = "${config.home.homeDirectory}/.local/share/obsidian-headless-npm";
  vaultPath = "${config.home.homeDirectory}/vault";
  secretsDirectory = "${config.home.homeDirectory}/.secrets";
  obsidianHeadlessConfigDirectory = "${config.home.homeDirectory}/.obsidian-headless";

  nodeGypBuildDependencies = lib.concatStringsSep ":" [
    "${nodejs}/bin"
    "${pkgs.python3}/bin"
    "${pkgs.gnumake}/bin"
  ];

  installObsidianHeadlessViaNpm = pkgs.writeShellScript "obsidian-headless-install" ''
    export NODE_GYP_PATH=${lib.escapeShellArg nodeGypBuildDependencies}
    export NPM_PREFIX=${lib.escapeShellArg npmPrefixDirectory}
    export OB_VERSION=${lib.escapeShellArg obsidianHeadlessVersion}
    export NPM_BIN=${nodejs}/bin/npm
    ${builtins.readFile ./scripts/install-obsidian-headless.sh}
  '';

  placeObsidianHeadlessSecrets = pkgs.writeShellScript "obsidian-headless-place-secrets" ''
    export SECRETS_DIR=${lib.escapeShellArg secretsDirectory}
    export CONFIG_DIR=${lib.escapeShellArg obsidianHeadlessConfigDirectory}
    export VAULT_PATH=${lib.escapeShellArg vaultPath}
    export PATH=${pkgs.gnused}/bin:$PATH
    ${builtins.readFile ./scripts/place-obsidian-headless-secrets.sh}
  '';

  obsidianHeadlessWrapper = pkgs.writeShellScriptBin "ob" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefixDirectory}"
    exec "${npmPrefixDirectory}/bin/ob" "$@"
  '';

  obsidianHeadlessSyncScript = pkgs.writeShellScript "obsidian-headless-sync" ''
    export NODE_BIN_DIR=${nodejs}/bin
    export NPM_PREFIX=${lib.escapeShellArg npmPrefixDirectory}
    export VAULT_PATH=${lib.escapeShellArg vaultPath}
    ${builtins.readFile ./scripts/obsidian-headless-sync.sh}
  '';

  inherit (pkgs.stdenv.hostPlatform) isDarwin isLinux;
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

  launchd.agents.obsidian-headless-sync = lib.mkIf isDarwin {
    enable = true;
    config = {
      Label = "com.dotfiles.obsidian-headless-sync";
      ProgramArguments = [
        "${pkgs.bash}/bin/bash"
        "${obsidianHeadlessSyncScript}"
      ];
      RunAtLoad = true;
      StartInterval = 300;
      StandardOutPath = "/tmp/obsidian-headless-sync.log";
      StandardErrorPath = "/tmp/obsidian-headless-sync.log";
    };
  };

  systemd.user = lib.mkIf isLinux {
    services.obsidian-headless-sync = {
      Unit = {
        Description = "Obsidian headless vault single-pass sync";
        After = [ "network.target" ];
      };

      Service = {
        Type = "oneshot";
        ExecStart = "${pkgs.bash}/bin/bash ${obsidianHeadlessSyncScript}";
      };
    };

    timers.obsidian-headless-sync = {
      Unit = {
        Description = "Periodic obsidian-headless vault sync every 300s";
      };

      Timer = {
        OnStartupSec = "60s";
        OnUnitActiveSec = "300s";
        Persistent = true;
      };

      Install = {
        WantedBy = [ "timers.target" ];
      };
    };

    startServices = "sd-switch";
  };
}
