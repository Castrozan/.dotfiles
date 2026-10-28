{
  config,
  lib,
  pkgs,
  ...
}:
let
  recoveryProgram = pkgs.writeText "pipewire-alsa-recovery.py" (
    builtins.readFile ./scripts/pipewire_alsa_recovery.py
  );
in
{
  systemd.user.services.pipewire-alsa-recovery = lib.mkIf config.services.pipewire.enable {
    description = "Recover PipeWire after persistent ALSA recovery failures";
    after = [ "pipewire.service" ];
    wantedBy = [ "default.target" ];
    unitConfig.ConditionGroup = "!gdm";
    path = [ pkgs.systemd ];
    serviceConfig = {
      ExecStart = "${pkgs.python312}/bin/python3 -u ${recoveryProgram}";
      Restart = "on-failure";
      RestartSec = 5;
      MemoryMax = "64M";
    };
  };
}
