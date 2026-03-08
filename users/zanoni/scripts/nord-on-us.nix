{ pkgs, ... }:
let
  nord-on-us = pkgs.writeShellScriptBin "nord-on-us" (
    builtins.readFile ../../../home/modules/network/scripts/nord-on-us
  );
in
{
  environment.systemPackages = [ nord-on-us ];
}
