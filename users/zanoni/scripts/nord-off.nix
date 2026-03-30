{ pkgs, ... }:
let
  buildSetuidRootScriptWrapper = import ./build-setuid-root-script-wrapper.nix { inherit pkgs; };
in
{
  security.wrappers.nord-off = {
    source = "${buildSetuidRootScriptWrapper ../../../home/modules/network/scripts/nord-off}";
    owner = "root";
    group = "root";
    setuid = true;
  };
}
