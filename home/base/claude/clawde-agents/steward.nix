{
  lib,
  hostname,
  ...
}:
let
  stewardPayloadRoot = ../clawde/agent-types/steward/payload;

  machinesRegistryPath = ../../../../private-config/machines.nix;
  machinesRegistry =
    if builtins.pathExists machinesRegistryPath then import machinesRegistryPath else { };

  peerAliases = builtins.filter (alias: alias != hostname) (builtins.attrNames machinesRegistry);

  peerEndpoints = builtins.listToAttrs (
    map (alias: {
      name = alias;
      value = {
        host = machinesRegistry.${alias}.tailscaleIp;
        user = machinesRegistry.${alias}.username;
        identity_file = "~/.ssh/id_ed25519";
      };
    }) peerAliases
  );

  peersConfiguration = {
    self = hostname;
    remote_inbox = "clawde/steward/inbox";
    peers = peerEndpoints;
  };

  personalityWithMachineIdentity = import ../clawde/inject-agent-identity.nix {
    inherit lib;
    self = hostname;
    peers = peerAliases;
    personality = builtins.readFile (stewardPayloadRoot + "/personality.md");
  };
in
{
  home.file."clawde/steward/peers.json".text = builtins.toJSON peersConfiguration;

  clawde.agents.steward = {
    type = "steward";
    personality = personalityWithMachineIdentity;
  };
}
