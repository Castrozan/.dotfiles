{ lib }:
let
  machineIdentityMapPath = ../../private-configuration/machines.nix;
  privateConfigPresent = builtins.pathExists machineIdentityMapPath;
  chiseMachineIdentity = lib.optionalAttrs privateConfigPresent (import machineIdentityMapPath).chise;
in
chiseMachineIdentity.tailscaleIp or "127.0.0.1"
