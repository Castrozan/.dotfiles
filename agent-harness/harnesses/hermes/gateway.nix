{
  config,
  lib,
  pkgs,
  ...
}:
let
  botProfileDirectory = name: ".hermes/profiles/${name}";

  botProfileFiles = name: _bot: {
    "${botProfileDirectory name}/plugins/dotfiles".source =
      config.home.file.".hermes/plugins/dotfiles".source;
    "${botProfileDirectory name}/plugins/claude-subscription-directsdk".source =
      config.home.file.".hermes/plugins/claude-subscription-directsdk".source;
    "${botProfileDirectory name}/.no-bundled-skills".text = "";
    "${botProfileDirectory name}/gateway.json".text = builtins.toJSON {
      platforms.discord.gateway_restart_notification = false;
    };
  };

  botProfileProvisioning = name: bot: [
    "${pkgs.python312}/bin/python3 ${./scripts/write-discord-bot-environment.py} %h/${botProfileDirectory name}/.env %h/.secrets/${bot.botTokenSecretName} ${bot.allowedDiscordUserId}"
    "${pkgs.coreutils}/bin/env HERMES_HOME=%h/${botProfileDirectory name} ${config.hermes.package}/bin/hermes --version"
  ];
in
{
  options.hermes.discordBots = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options = {
          botTokenSecretName = lib.mkOption {
            type = lib.types.str;
            description = "Secret under ~/.secrets holding the Discord bot token.";
          };
          allowedDiscordUserId = lib.mkOption {
            type = lib.types.str;
            description = "The only Discord user the bot answers.";
          };
        };
      }
    );
    default = { };
    description = "Hermes profiles the host gateway serves as Discord bots, keyed by profile name.";
  };

  config = {
    home.file = lib.mkMerge (lib.mapAttrsToList botProfileFiles config.hermes.discordBots);

    systemd.user.services.hermes-agent = {
      Unit.Description = "Hermes Agent gateway";
      Install.WantedBy = [ "default.target" ];
      Service = {
        Environment = [
          "PATH=/run/wrappers/bin:${config.home.profileDirectory}/bin:/run/current-system/sw/bin"
        ];
        ExecStartPre = lib.concatLists (
          lib.mapAttrsToList botProfileProvisioning config.hermes.discordBots
        );
        ExecStart = "${config.hermes.package}/bin/hermes gateway run --replace --external-supervisor";
        WorkingDirectory = config.home.homeDirectory;
        KillMode = "mixed";
        Restart = "always";
        RestartSec = "5s";
        RestartPreventExitStatus = 78;
      };
    };
  };
}
