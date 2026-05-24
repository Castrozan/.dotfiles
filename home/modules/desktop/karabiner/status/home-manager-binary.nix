{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "karabiner-status" ''
      exec ${pkgs.python312}/bin/python3 ${./scripts/karabiner-status} "$@"
    '')
  ];
}
