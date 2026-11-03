{ pkgs, ... }:
let
  forwardToChise =
    command:
    pkgs.writeShellScriptBin command ''
      exec ssh chise ${command} "$(printf '%q ' "$@")"
    '';
in
{
  home.packages = map forwardToChise [
    "avatar-talk"
    "avatar-command"
  ];
}
