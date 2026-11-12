{ pkgs, ... }:
let
  forwardToChise =
    command:
    pkgs.writeShellScriptBin command ''
      exec ssh chise ${command} "$(printf '%q ' "$@")"
    '';
  talk = pkgs.writeShellScriptBin "avatar-talk" ''
    exec ${pkgs.python312}/bin/python3 ${./scripts/conversation/remote_seat}/remote_talk.py "$@"
  '';
in
{
  home.packages = [
    talk
    (forwardToChise "avatar-command")
  ];
}
