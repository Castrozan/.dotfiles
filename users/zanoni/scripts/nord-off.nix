{ pkgs, ... }:
let
  script = builtins.readFile ../../../bin/nord-off;
in
let
  nord-off = pkgs.writeShellScriptBin "nord-off" ''
    ${script}
  '';
in
{
  environment.systemPackages = [ nord-off ];
}
