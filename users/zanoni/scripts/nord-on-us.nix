{ pkgs, ... }:
let
  buildSetuidRootScriptWrapper = import ./build-setuid-root-script-wrapper.nix { inherit pkgs; };
in
{
  security.wrappers.nord-on-us = {
    source = "${buildSetuidRootScriptWrapper ../../../home/base/network/scripts/nord-on-us}";
    owner = "root";
    group = "root";
    setuid = true;
  };
}
