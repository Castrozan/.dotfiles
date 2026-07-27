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

  remoteCiTestingDirective = ''

    <testing-is-remote-ci>
    On one point this fleet supersedes the local-green definition in your steward skill: running the repo's test suite is CI's job, not yours. Green on this machine means `git pull --ff-only` clean plus a successful rebuild plus a passing `health-check`, so never run the suite as a gate and never hold a push waiting on one. Publish the commit, then take the test verdict from the run it triggers, waiting the run out with `dotfiles-ci`, which polls every GitHub Actions run for that commit, prints each outcome and exits non-zero when one is red or never appears. Everything your skill says about CI still holds: a red CI is the fleet's top-priority breakage you fix per `<fixing>`, a pending CI is never `clean`, and a runner-infra flake is re-run rather than patched. Every job reports all of its failures instead of dying on the first, so read the whole run and fix the batch in one push rather than one error per push. The integration and runtime tiers need the live machine and CI cannot reach them, so a nightly 03:00 job owns them; never run those tiers from a heartbeat tick, and treat a red nightly log exactly like a red CI.
    </testing-is-remote-ci>
  '';

  effectivePersonality =
    personalityWithMachineIdentity + machineLocalWrapperDirective + remoteCiTestingDirective;
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
