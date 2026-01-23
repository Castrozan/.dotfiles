{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/volume;

  volume = pkgs.writeShellScriptBin "volume" ''
    ${script}
  '';
in
{
  home.packages = [ volume ];
}
