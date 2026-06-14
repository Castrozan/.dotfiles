{ config, ... }:
let
  machinesRegistryPath = ../../../private-config/machines.nix;
in
{
  clawde = {
    machinesRegistry =
      if builtins.pathExists machinesRegistryPath then import machinesRegistryPath else { };

    stewardLiveCheckoutPayloadPath = "${config.home.homeDirectory}/.dotfiles/home/base/claude/clawde/agent-types/steward/payload";

    claudePackage = config.claude.package;
  };
}
