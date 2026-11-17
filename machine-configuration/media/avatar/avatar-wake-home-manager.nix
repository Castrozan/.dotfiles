{
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
    }:$PATH
    export AVATAR_AGENT_HOST=${hostname}
    export AVATAR_PEER_HOSTS="${lib.concatStringsSep " " peerHosts}"
    export AVATAR_SERVANT_CHARACTERS=${programs.servantCharacters}
    export AVATAR_ORDINARY_WORDS=${programs.ordinaryWords}
    export PYTHONPATH=${./scripts/listening}:${./scripts/echo}:${./scripts/conversation}:${./scripts/wake}:${programs.a2aLibrary}
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
        Restart = "always";
        RestartSec = 5;
      };
      Install.WantedBy = [ "graphical-session.target" ];
    };
  };
}
