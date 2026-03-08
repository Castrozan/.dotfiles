{ pkgs, ... }:
let
  nord-off = pkgs.writeShellScriptBin "nord-off" (
    builtins.readFile ../../../home/modules/network/scripts/nord-off
  );
in
{
  environment.systemPackages = [ nord-off ];
}
