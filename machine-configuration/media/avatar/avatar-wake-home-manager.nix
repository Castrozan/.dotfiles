{
  pkgs,
  lib,
  inputs,
  isNixOS,
  ...
}:
let
  programs = import ./avatar-programs.nix { inherit pkgs lib inputs; };
  wake = pkgs.writeShellScriptBin "avatar-wake" ''
    export PATH=${
      lib.makeBinPath [
        programs.a2a
        programs.herdr
        programs.talk
        pkgs.pulseaudio
        pkgs.systemd
      ]
    }:$PATH
    export PYTHONPATH=${./scripts/listening}:${./scripts/conversation}:${./scripts/wake}:${programs.a2aLibrary}
    exec ${pkgs.python312}/bin/python3 ${./scripts/wake/wake_listener.py} "$@"
  '';
in
{
  config = lib.mkIf isNixOS {
    home.packages = [ wake ];
    systemd.user.services.avatar-wake = {
      Unit = {
        Description = "Wake a live agent session by its Servant name";
        After = [
          "graphical-session.target"
          "hex.service"
        ];
        PartOf = [ "graphical-session.target" ];
        Wants = [ "hex.service" ];
      };
      Service = {
        ExecStart = "${wake}/bin/avatar-wake";
        Restart = "on-failure";
        RestartSec = 5;
      };
      Install.WantedBy = [ "graphical-session.target" ];
    };
  };
}
