{
  pkgs,
  lib,
  inputs,
  isNixOS,
  ...
}:
let
  programs = import ./avatar-programs.nix { inherit pkgs lib; };
  herdr = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
  a2a = import ../../../agent-harness/agent-to-agent-communication/client/a2a-client-package.nix {
    inherit pkgs;
  };
  a2aLibrary = lib.concatStringsSep ":" [
    "${../../../agent-harness/agent-to-agent-communication/client/scripts}"
    "${../../../agent-harness/servants}"
    "${../../../agent-harness/hooks/runtime/common}"
  ];
  wake = pkgs.writeShellScriptBin "avatar-wake" ''
    export PATH=${
      lib.makeBinPath [
        a2a
        herdr
        programs.talk
        pkgs.pulseaudio
        pkgs.systemd
      ]
    }:$PATH
    export PYTHONPATH=${./scripts/listening}:${./scripts/conversation}:${./scripts/wake}:${a2aLibrary}
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
