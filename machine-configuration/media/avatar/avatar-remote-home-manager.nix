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
  forwardToChise =
    command:
    pkgs.writeShellScriptBin command ''
      exec ssh chise ${command} "$(printf '%q ' "$@")"
    '';
  talk = pkgs.writeShellScriptBin "avatar-talk" ''
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
    export AVATAR_AGENT_HOST=${hostname}
    export AVATAR_WAKE_PAGE=${./scripts/wake/page}
    export AVATAR_SEAT_PAGE=${./scripts/conversation/remote_seat/page}
    export PYTHONPATH=${./scripts/listening}:${./scripts/echo}:${./scripts/conversation}:${./scripts/conversation/remote_seat}:${./scripts/wake}:${programs.a2aLibrary}
    exec ${websocketPython}/bin/python3 ${./scripts/wake}/wake_listener.py "$@"
  '';
  wakeLog = "${config.home.homeDirectory}/Library/Logs/avatar-wake.log";
in
{
  home.packages = [
    talk
    wake
    (forwardToChise "avatar-command")
  ];

  launchd.agents.avatar-wake = {
    enable = true;
    config = {
      ProgramArguments = [ "${wake}/bin/avatar-wake" ];
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = wakeLog;
      StandardErrorPath = wakeLog;
    };
  };
}
