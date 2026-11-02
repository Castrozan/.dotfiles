{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "avatar-talk" ''
      exec ssh chise avatar-talk "$(printf '%q ' "$@")"
    '')
  ];
}
