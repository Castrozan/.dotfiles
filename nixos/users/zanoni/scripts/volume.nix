{ pkgs, ... }:
let
  script = builtins.readFile ../../../../bin/volume;
in
let
  volume = pkgs.writeShellScriptBin "volume" ''
    ${script}
  '';
in
{
  environment.systemPackages = [ volume ];
}
