{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "shorten-url" ''
      exec ${pkgs.python312}/bin/python3 ${./scripts/shorten_url.py} "$@"
    '')
  ];
}
