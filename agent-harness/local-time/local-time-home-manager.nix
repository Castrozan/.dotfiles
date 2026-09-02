{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "local-time" ''
      exec ${pkgs.python312}/bin/python3 ${./local_time.py} "$@"
    '')
  ];
}
