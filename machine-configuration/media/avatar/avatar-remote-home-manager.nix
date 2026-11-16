{
  pkgs,
  lib,
  inputs,
  config,
  hostname,
  ...
}:
let
  programs = import ./avatar-programs.nix { inherit pkgs lib inputs; };
  topology = import ./home-manager/avatar-topology.nix;
  rebuildSafeLaunchAgentLib =
    import ../../operating-system/launchd/rebuild-safe-launch-agent-library.nix
      {
        inherit config lib pkgs;
      };
  forwardToHost =
    command:
    pkgs.writeShellScriptBin command ''
      exec ssh ${topology.host} ${command} "$(printf '%q ' "$@")"
    '';
  forwardCommandToHost = pkgs.writeShellScriptBin "avatar-command" ''
    if [ "''${1:-}" = speak ] && [ -n "''${HERDR_PANE_ID:-}" ]; then
      ssh -n ${topology.host} avatar-claim-floor --speaker "$(printf '%q' "${hostname}:$HERDR_PANE_ID")" || exit 1
    fi
    exec ssh ${topology.host} avatar-command "$(printf '%q ' "$@")"
  '';
  remoteMeeting =
    verb: command:
    pkgs.writeShellScriptBin command ''
      export AVATAR_HOST=${topology.host}
      exec ${pkgs.python312}/bin/python3 ${./scripts/conversation/remote_seat}/remote_meeting.py ${verb} "$@"
    '';
  talk = pkgs.writeShellScriptBin "avatar-talk" ''
    export AVATAR_HOST=${topology.host}
    export AVATAR_AGENT_HOST=${hostname}
    exec ${pkgs.python312}/bin/python3 ${./scripts/conversation/remote_seat}/remote_talk.py "$@"
  '';
  websocketPython = pkgs.python312.withPackages (packages: [ packages.websockets ]);
  wake = pkgs.writeShellScriptBin "avatar-wake" ''
    export PATH=${
      lib.makeBinPath [
        programs.a2a
        programs.herdr
        talk
      ]
    }:$PATH
    export AVATAR_HOST=${topology.host}
    export AVATAR_AGENT_HOST=${hostname}
    export AVATAR_ORDINARY_WORDS=${programs.ordinaryWords}
    export AVATAR_WAKE_PAGE=${./scripts/wake/page}
    export AVATAR_SEAT_PAGE=${./scripts/conversation/remote_seat/page}
    export PYTHONPATH=${./scripts/listening}:${./scripts/echo}:${./scripts/conversation}:${./scripts/conversation/remote_seat}:${./scripts/wake}:${programs.a2aLibrary}
    exec ${websocketPython}/bin/python3 ${./scripts/wake}/wake_listener.py "$@"
  '';
  doctor = import ./home-manager/avatar-doctor-package.nix {
    inherit pkgs lib;
    commands = [ talk ];
    arguments = "--seat-of ${topology.host}";
  };
  wakeLog = "${config.home.homeDirectory}/Library/Logs/avatar-wake.log";
  wakeLaunchAgent = rebuildSafeLaunchAgentLib.mkRebuildSafeLaunchAgent {
    name = "avatar-wake";
    label = "com.dotfiles.avatar-wake";
    package = wake;
    executableName = "avatar-wake";
    restartWhenPackageChanges = true;
    serviceConfig = {
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = wakeLog;
      StandardErrorPath = wakeLog;
    };
  };
in
lib.mkMerge [
  {
    home.packages = [
      talk
      wake
      doctor
      forwardCommandToHost
      (forwardToHost "avatar-audio")
      (remoteMeeting "start" "avatar-start")
      (remoteMeeting "stop" "avatar-stop")
      (remoteMeeting "controls" "avatar-controls")
      (remoteMeeting "listen" "avatar-listen")
    ];
  }
  wakeLaunchAgent
]
