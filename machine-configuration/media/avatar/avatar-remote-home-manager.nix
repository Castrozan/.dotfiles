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
  remoteMeeting =
    verb: command:
    pkgs.writeShellScriptBin command ''
      export AVATAR_HOST=${topology.host}
      export PYTHONPATH=${./scripts/listening}
      exec ${pkgs.python312}/bin/python3 ${./scripts/conversation/remote_seat}/remote_meeting.py ${verb} "$@"
    '';
  conversation = import ./home-manager/avatar-mac-conversation.nix {
    inherit
      pkgs
      lib
      programs
      hostname
      ;
    inherit (topology) host;
  };
  inherit (conversation) talk;
  peerHosts = lib.filter (machine: machine != hostname) topology.machines;
  websocketPython = pkgs.python312.withPackages (packages: [ packages.websockets ]);
  wake = pkgs.writeShellScriptBin "avatar-wake" ''
    export PATH=${
      lib.makeBinPath [
        programs.a2a
        programs.herdr
        conversation.command
        talk
      ]
    }:$PATH
    export AVATAR_HOST=${topology.host}
    export AVATAR_AGENT_HOST=${hostname}
    export AVATAR_PEER_HOSTS="${lib.concatStringsSep " " peerHosts}"
    export AVATAR_ORDINARY_WORDS=${programs.ordinaryWords}
    export AVATAR_SERVANT_CHARACTERS=${programs.servantCharacters}
    export AVATAR_WAKE_PAGE=${./scripts/wake/page}
    export AVATAR_SEAT_PAGE=${./scripts/conversation/remote_seat/page}
    export PYTHONPATH=${conversation.modules}:${programs.a2aLibrary}
    exec ${websocketPython}/bin/python3 ${./scripts/wake}/wake_listener.py "$@"
  '';
  doctor = import ./home-manager/avatar-doctor-package.nix {
    inherit pkgs lib;
    commands = [
      talk
      programs.transcribe
    ];
    arguments = "--seat-of ${topology.host}";
  };
  conversationLog = "${config.home.homeDirectory}/Library/Logs/avatar-conversation.log";
  onDemandAgent =
    name: package: executableName:
    rebuildSafeLaunchAgentLib.mkRebuildSafeLaunchAgent {
      inherit name package executableName;
      label = "com.dotfiles.${name}";
      serviceConfig = {
        KeepAlive = false;
        RunAtLoad = false;
        StandardOutPath = conversationLog;
        StandardErrorPath = conversationLog;
      };
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
      programs.transcribe
      conversation.command
      (forwardToHost "avatar-audio")
      (remoteMeeting "start" "avatar-start")
      (remoteMeeting "stop" "avatar-stop")
      (remoteMeeting "controls" "avatar-controls")
      (remoteMeeting "listen" "avatar-listen")
    ];
  }
  wakeLaunchAgent
  (onDemandAgent "avatar-conversation" conversation.listener "avatar-conversation-listener")
  (onDemandAgent "avatar-control" conversation.controlServer "avatar-control-server")
  (onDemandAgent "avatar-renderer" conversation.renderer "avatar-renderer-server")
]
