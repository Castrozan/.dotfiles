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
  programs = import ../avatar-programs.nix {
    inherit
      pkgs
      lib
      inputs
      hostname
      ;
  };
  voiceHolder = pkgs.writeShellScriptBin "avatar-voice-holder" ''
    export PATH=${
      lib.makeBinPath [
        programs.talk
        programs.command
        pkgs.systemd
      ]
    }:$PATH:${config.home.profileDirectory}/bin
    export AVATAR_SERVANT_CHARACTERS=${programs.servantCharacters}
    export PYTHONPATH=${../scripts}:${../scripts/audio_graph}:${../scripts/listening}:${../scripts/echo}:${../scripts/conversation}:${../scripts/wake}:${../scripts/holder}
    exec ${pkgs.python312}/bin/python3 ${../scripts/holder}/voice_holder_cli.py "$@"
  '';
in
{
  config = lib.mkIf isNixOS { home.packages = [ voiceHolder ]; };
}
