{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  syntheticProfiles = [
    {
      name = "work";
      directoryPrefixes = [ "~/repo" ];
      gitRemotePatterns = [ "gitlab.example.com" ];
      instructionFiles = [ ];
      claudeCode.settingsOverlay.enabledPlugins."tooling@internal" = true;
      codex = { };
      opencode = { };
    }
    {
      name = "personal";
      directoryPrefixes = [ "~/side-projects" ];
      gitRemotePatterns = [ ];
      instructionFiles = [ ];
      claudeCode = { };
      codex = { };
      opencode = { };
    }
  ];

  routingTable =
    builtins.fromJSON
      (import ../routing/routing-table.nix {
        inherit pkgs;
        workspaceProfiles = syntheticProfiles;
      }).text;

  routedProfileKeys = lib.unique (builtins.concatMap builtins.attrNames routingTable.profiles);

  inherit (import ../activation/harness-launch-dispatch.nix { inherit lib; })
    mkWorkspaceProfileLaunchDispatch
    ;

  resolverExecutable = "/nix/store/synthetic-resolver/bin/resolve-workspace-profile";

  dispatchFor =
    profiles:
    mkWorkspaceProfileLaunchDispatch {
      agentWorkspaceProfiles = { inherit profiles resolverExecutable; };
      activationShellStatementsForProfile =
        workspaceProfile: "activatedWorkspaceProfile=${workspaceProfile.name}";
    };

  dispatchFragment = dispatchFor syntheticProfiles;

  containsText = haystack: needle: lib.hasInfix needle haystack;

  claudeConfiguration = helpers.homeManagerTestConfiguration [
    ../../harnesses/claude-code
    ../../agent-instructions/interactive-skill-catalog/interactive-skill-index-home-manager.nix
    { claude.requiredWorkspaceProfileName = "test-profile"; }
  ];
  codexConfiguration = helpers.homeManagerTestConfiguration [ ../../harnesses/codex ];
  opencodeConfiguration = helpers.homeManagerTestConfiguration [ ../../harnesses/opencode ];

  wrapperText =
    configuration: wrapperName:
    (lib.findFirst (package: (package.name or "") == wrapperName) null configuration.home.packages)
    .text;

  claudeWrapperText = wrapperText claudeConfiguration "claude";
  codexWrapperText = wrapperText codexConfiguration "codex";
  opencodeWrapperText = wrapperText opencodeConfiguration "opencode";
in
{
  workspace-profile-routing-table-carries-every-declared-profile =
    mkEvalCheck "workspace-profile-routing-table-carries-every-declared-profile"
      (
        map (routedProfile: routedProfile.name) routingTable.profiles == [
          "work"
          "personal"
        ]
      )
      "the resolver only ever sees this table, so a profile missing from it can never be routed to no matter how completely it is declared";

  workspace-profile-routing-table-carries-selectors-only =
    mkEvalCheck "workspace-profile-routing-table-carries-selectors-only"
      (
        routedProfileKeys == [
          "directoryPrefixes"
          "gitRemotePatterns"
          "name"
        ]
      )
      "the routing table is the resolver's whole input and is world-readable in the nix store; widening it to the harness payload sections would both rebuild the resolver on every payload edit and publish payload contents that belong to the harness wrappers alone";

  workspace-profile-dispatch-branches-on-every-profile =
    mkEvalCheck "workspace-profile-dispatch-branches-on-every-profile"
      (
        containsText dispatchFragment "activatedWorkspaceProfile=work"
        && containsText dispatchFragment "activatedWorkspaceProfile=personal"
      )
      "a profile without a dispatch branch resolves by name and then silently activates nothing, which reads exactly like the global configuration and hides the failure";

  workspace-profile-dispatch-asks-the-resolver-about-the-launch-directory =
    mkEvalCheck "workspace-profile-dispatch-asks-the-resolver-about-the-launch-directory"
      (containsText dispatchFragment ''${resolverExecutable} --working-directory "$PWD"'')
      "routing exists so the human never has to remember a launcher; resolving anything other than the directory the wrapper was launched from returns the wrong profile without any visible error";

  workspace-profile-dispatch-costs-nothing-when-no-profile-is-declared =
    mkEvalCheck "workspace-profile-dispatch-costs-nothing-when-no-profile-is-declared"
      (dispatchFor [ ] == "")
      "every harness wrapper embeds this fragment, so an unconditional resolver call would add a python process to every launch on machines that declare no profile at all";

  claude-applies-the-resolved-workspace-profile =
    mkEvalCheck "claude-applies-the-resolved-workspace-profile"
      (
        containsText claudeWrapperText "workspaceProfileArguments"
        && containsText claudeWrapperText "claudeSystemPromptFile"
      )
      "claude activation lands as extra argv and a swapped system-prompt file; a wrapper refactor that stops splicing either one leaves routing resolving correctly and applying nothing";

  claude-required-workspace-profile-cannot-be-forced-from-the-calling-shell =
    mkEvalCheck "claude-required-workspace-profile-cannot-be-forced-from-the-calling-shell"
      (
        containsText claudeWrapperText "unset AGENT_WORKSPACE_PROFILE AGENT_WORKSPACE_PROFILE_ROUTING_TABLE"
        && containsText claudeWrapperText "Claude is restricted to the %s workspace profile on this machine"
      )
      "a caller-controlled profile or routing table must not bypass a machine's Claude launch restriction";

  codex-applies-the-resolved-workspace-profile =
    mkEvalCheck "codex-applies-the-resolved-workspace-profile"
      (
        containsText codexWrapperText "workspaceProfileArguments"
        && containsText codexWrapperText "codexDeveloperInstructionsFile"
      )
      "codex activation lands as -c overrides and a swapped developer-instructions file; dropping either from the wrapper silently reverts every profiled directory to the global codex configuration";

  opencode-applies-the-resolved-workspace-profile =
    mkEvalCheck "opencode-applies-the-resolved-workspace-profile"
      (containsText opencodeWrapperText "opencodeConfigOverlayFile")
      "opencode has no launch flag for this, so the profile can only arrive through the OPENCODE_CONFIG overlay the wrapper exports; hardcoding that export back to the base overlay disables routing for opencode alone";

  every-harness-reads-the-same-workspace-profile-declarations =
    mkEvalCheck "every-harness-reads-the-same-workspace-profile-declarations"
      (
        claudeConfiguration.agentWorkspaceProfiles.routingTableFile
        == codexConfiguration.agentWorkspaceProfiles.routingTableFile
        &&
          codexConfiguration.agentWorkspaceProfiles.routingTableFile
          == opencodeConfiguration.agentWorkspaceProfiles.routingTableFile
      )
      "one declaration per machine is the whole point of routing outside the harnesses; a harness that built its own table would drift from the others the first time a profile changed";
}
