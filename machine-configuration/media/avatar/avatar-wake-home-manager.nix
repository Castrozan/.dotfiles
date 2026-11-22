{
  config,
  pkgs,
  lib,
  inputs,
  isNixOS,
  hostname,
  ...
}:
let
  programs = import ./avatar-programs.nix { inherit pkgs lib inputs; };
  topology = import ./home-manager/avatar-topology.nix;
  switchLatency = import ./home-manager/avatar-switch-latency-package.nix { inherit pkgs; };
  peerHosts = lib.filter (machine: machine != hostname) topology.machines;
  wake = pkgs.writeShellScriptBin "avatar-wake" ''
    export PATH=${
      lib.makeBinPath [
        programs.a2a
        programs.command
        programs.herdr
        programs.talk
        pkgs.openssh
        pkgs.pulseaudio
        pkgs.systemd
      ]
    }:$PATH:${config.home.profileDirectory}/bin
    export AVATAR_AGENT_HOST=${hostname}
    export AVATAR_PEER_HOSTS="${lib.concatStringsSep " " peerHosts}"
    export AVATAR_SERVANT_CHARACTERS=${programs.servantCharacters}
    export AVATAR_ORDINARY_WORDS=${programs.ordinaryWords}
    export PYTHONPATH=${./scripts/listening}:${./scripts/echo}:${./scripts/conversation}:${./scripts/wake}:${./scripts/addressing}:${programs.a2aLibrary}
    exec ${pkgs.python312}/bin/python3 ${./scripts/wake/wake_listener.py} "$@"
  '';
in
{
  config = lib.mkIf isNixOS {
    home.packages = [
      wake
      switchLatency
    ];
    systemd.user = {
      services = {
        avatar-switch-latency = {
          Unit.Description = "Keep the measured avatar switch round trips past wake log rotation";
          Service = {
            Type = "oneshot";
            ExecStart = "${switchLatency}/bin/avatar-switch-latency --record";
          };
        };
        avatar-wake = {
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
            Restart = "always";
            RestartSec = 5;
          };
          Install.WantedBy = [ "graphical-session.target" ];
        };
      };
      timers.avatar-switch-latency = {
        Unit.Description = "Daily keep of the measured avatar switch round trips";
        Timer = {
          OnCalendar = "daily";
          Persistent = true;
        };
        Install.WantedBy = [ "timers.target" ];
      };
    };
  };
}
