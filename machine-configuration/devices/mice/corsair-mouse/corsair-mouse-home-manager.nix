{ pkgs, ... }:
let
  pythonWithHidapi = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.hid ]);
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "corsair-mouse-brightness" ''
      exec ${pythonWithHidapi}/bin/python3 ${./scripts/corsair_mouse_brightness.py} "$@"
    '')
  ];
}
