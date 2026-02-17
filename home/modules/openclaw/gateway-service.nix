{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  inherit (config.home) homeDirectory username;
  homeDir = homeDirectory;
  nodejs = pkgs.nodejs_22;
  prefix = "$HOME/.local/share/openclaw-npm";

  nixSystemPaths = lib.concatStringsSep ":" [
    "${nodejs}/bin"
    "${pkgs.git}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  gatewayScript = pkgs.writeShellScript "openclaw-gateway" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${prefix}"

    OPENCLAW_BIN="${prefix}/bin/openclaw"
    if [ ! -x "$OPENCLAW_BIN" ]; then
      echo "OpenClaw not installed yet. Run 'openclaw --version' first to trigger auto-install."
      exit 1
    fi

    exec "$OPENCLAW_BIN" gateway --port ${toString openclaw.gatewayPort}
  '';
in
{
  options.openclaw.gatewayService.enable = lib.mkEnableOption "OpenClaw gateway systemd user service";

  config = lib.mkIf openclaw.gatewayService.enable {
    systemd.user.services.openclaw-gateway = {
      Unit = {
        Description = "OpenClaw Gateway (port ${toString openclaw.gatewayPort})";
        After = [ "network.target" ];
      };

      Service = {
        Type = "simple";
        ExecStart = "${gatewayScript}";
        Restart = "always";
        RestartSec = "5s";
        Environment = [
          "PATH=${nixSystemPaths}"
          "NODE_ENV=production"
          "OPENCLAW_NIX_MODE=1"
        ];
      };

      Install = {
        WantedBy = [ "default.target" ];
      };
    };
  };
}
