{
  lib,
  hostname,
  inputs,
  pkgs,
  config,
  isDarwin,
  ...
}:
let
  stewardPayloadRoot = inputs.clawde.stewardPayloadPath;

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
    + localInstructions.repoCiToolingDirective
    + localInstructions.repoActivationDirective;

  configurationDirectory =
    if localWrapperRepoPath != null then
      localWrapperRepoPath
    else
      "${config.home.homeDirectory}/.dotfiles";
  configurationAttribute =
    if isDarwin then
      "darwinConfigurations.${hostname}.system.outPath"
    else
      "nixosConfigurations.${hostname}.config.system.build.toplevel.outPath";
  configurationReference = "git+file://${configurationDirectory}?submodules=1#${configurationAttribute}";

  stewardRebuild = pkgs.writeShellScriptBin "steward-rebuild" ''
    exec ${pkgs.python312}/bin/python3 ${../scripts/steward_rebuild.py} \
      --configuration ${lib.escapeShellArg configurationReference} "$@"
  '';
in
{
  home.packages = [ stewardRebuild ];

  clawdeAgentSkillSets.steward = [
    "coding"
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
    harness = "codex";
    harnessFallbackChain = [
      "claude"
      "opencode"
    ];
    modelByHarness = {
      claude = "sonnet";
      codex = "gpt-5.6-terra";
      opencode = "opencode/ling-3.0-flash-fin-free";
    };
    reasoningEffort = "high";
    personality = effectivePersonality;
    launchOnTrigger = false;
    heartbeatGateCommand = lib.mkIf (hostname == "rin") ''
      ${stewardRebuild}/bin/steward-rebuild --state-directory ${lib.escapeShellArg "${config.home.homeDirectory}/clawde/steward/state/rebuild"} >/dev/null
      clawde-heartbeat-change-gate --label steward --retries-while-pending 2 --probe steward-heartbeat-probe
    '';
    mcpServers = { };
    expose.a2a.agentDescriptionForCard = "keeps every machine's checkout synced, green and pushed";
  };
}
