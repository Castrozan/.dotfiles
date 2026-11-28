{ pkgs, ... }:
let
  servantsDomain = ./.;
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "servant-name" ''
      exec ${pkgs.python312}/bin/python3 ${servantsDomain}/servant_name.py "$@"
    '')
  ];
}
