{ config, ... }:
{
  home.activation.removeOrphanNixDarwinKarabinerLaunchdEntries =
    config.lib.dag.entryAfter [ "setupLaunchAgents" ]
      ''
        /bin/sh ${./scripts/remove-orphan-nix-darwin-karabiner-launchd-entries}
      '';
}
