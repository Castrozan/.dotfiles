{ pkgs, ... }:
let
  buildSetuidRootScriptWrapper = import ./build-setuid-root-script-wrapper.nix { inherit pkgs; };
in
{
  security.wrappers.nord-on = {
    source = "${buildSetuidRootScriptWrapper ../../../home/modules/network/scripts/nord-on}";
    owner = "root";
    group = "root";
    setuid = true;
  };
}
