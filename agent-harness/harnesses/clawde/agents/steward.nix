{
  lib,
  hostname,
  inputs,
  pkgs,
  ...
}:
let
  stewardPayloadRoot = inputs.clawde.stewardPayloadPath;
  forgeTools = import ./steward/forge-tools.nix { inherit inputs pkgs lib; };

  machinesRegistryPath = ../../../../private-configuration/machines.nix;
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

  personalityWithMachineIdentity = inputs.clawde.injectAgentIdentity {
    inherit lib;
    self = hostname;
    peers = peerAliases;
    personality = builtins.readFile (stewardPayloadRoot + "/personality.md");
  };

  localWrapperRepoPath = machinesRegistry.${hostname}.localWrapperRepoPath or null;

  localInstructions = import ./steward/instructions.nix {
    inherit lib hostname localWrapperRepoPath;
  };

  effectivePersonality =
    personalityWithMachineIdentity
    + localInstructions.machineLocalWrapperDirective
    + localInstructions.repoCiToolingDirective;
in
{
  imports = [
    ./steward/validation-resource-bound.nix
    ./steward/cycle
  ];

  home.packages = forgeTools.profilePackages;
  clawde.agentTypes.steward.packages = lib.mkForce forgeTools.packages;

  clawdeAgentSkillSets.steward = [
    "coding"
    "forge"
    "ci-watcher"
    "nix"
    "deep-work"
    "workspace"
    "herdr"
    "agent-session"
    "notify"
    "review"
  ];

  home.file."clawde/steward/peers.json".text = builtins.toJSON peersConfiguration;

  clawde.agents.steward = {
    type = "steward";
    harness = "claude";
    harnessFallbackChain = [
      "codex"
      "opencode"
    ];
    modelByHarness = {
      claude = "sonnet";
      codex = "gpt-6.1-terra";
      opencode = "opencode/ling-3.0-flash-fin-free";
    };
    reasoningEffort = "high";
    personality = effectivePersonality;
    mcpServers = { };
    expose.a2a.agentDescriptionForCard = "keeps every machine's checkout synced, green and pushed";
  };
}
