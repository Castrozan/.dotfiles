{ config, ... }:
{
  systemd.user.services.hermes-agent = {
    Unit.Description = "Hermes Agent gateway";
    Install.WantedBy = [ "default.target" ];
    Service = {
      Environment = [
        "PATH=/run/wrappers/bin:${config.home.profileDirectory}/bin:/run/current-system/sw/bin"
      ];
      ExecStart = "${config.hermes.package}/bin/hermes gateway run --replace --external-supervisor";
      WorkingDirectory = config.home.homeDirectory;
      KillMode = "mixed";
      Restart = "always";
      RestartSec = "5s";
      RestartPreventExitStatus = 78;
    };
  };
}
