{
  lib,
  hostname,
  inputs,
  buildClawdeAgentMcpConfigFile,
  ...
}:
let
  stewardPayloadRoot = inputs.clawde.stewardPayloadPath;

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

  personalityWithMachineIdentity = inputs.clawde.injectAgentIdentity {
    inherit lib;
    self = hostname;
    peers = peerAliases;
    personality = builtins.readFile (stewardPayloadRoot + "/personality.md");
  };

  localWrapperRepoPath = machinesRegistry.${hostname}.localWrapperRepoPath or null;

  machineLocalWrapperDirective = lib.optionalString (localWrapperRepoPath != null) ''

    <machine-local-wrapper-repo>
    Beyond the shared dotfiles checkout, ${hostname} also owns a private machine-local wrapper repo at ${localWrapperRepoPath}: a standalone git repo with its own origin, not a submodule and not part of the fleet, no CI and no peer stewards, whose flake is what this machine actually builds by importing the public dotfiles and layering a private overlay on top. Keep it reconciled with its own origin/main under the same invariant you hold for the dotfiles repo: pull `--ff-only` when it is behind, and when it holds validated local commits ahead and the machine builds green, push it fast-forward-only; never `git push --force`, never reset or rewrite history to force agreement, stage specific files only, and escalate to the operator on any non-fast-forward divergence you cannot cleanly resolve. Its green proof is the ordinary rebuild you already run for this machine, since that rebuild reads this wrapper. Treat it purely as a second repo you keep synced, never a peer to coordinate with, and never let its private contents cross into the shared dotfiles repo.
    </machine-local-wrapper-repo>
  '';

  repoCiToolingDirective = ''

    <repo-ci-tooling>
    The CI-watching command your skill sends you to is `dotfiles-ci`: it polls every GitHub Actions run for a commit, prints each run's outcome and exits non-zero when one is red or never appears. The integration and runtime tiers need the live machine, so a nightly 03:00 job owns them and no tick of yours ever runs them; a red nightly log under `~/.local/state/dotfiles-nightly-tests` is repo breakage you fix like a red CI.
    </repo-ci-tooling>
  '';

  effectivePersonality =
    personalityWithMachineIdentity + machineLocalWrapperDirective + repoCiToolingDirective;
in
{
  claudeCuratedSkillSets.steward = [
    "git"
    "nix"
    "test"
    "deep-work"
    "workspace"
    "worktrees"
    "herdr"
    "exit"
    "restart"
    "notify"
    "review"
  ];

  home.file."clawde/steward/peers.json".text = builtins.toJSON peersConfiguration;

  clawde.agents.steward = {
    type = "steward";
    personality = effectivePersonality;
    launchOnTrigger = false;
    mcpConfigFile = buildClawdeAgentMcpConfigFile "steward" [ "a2a" ];
  };
}
