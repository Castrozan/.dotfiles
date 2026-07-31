{
  helpers,
  self,
}:
let
  bothHarnessModules = [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    self.homeManagerModules.codex
    self.homeManagerModules.opencode
    {
      claudeCuratedSkillSets.harness-check-set = [ "research" ];
      clawde.agents = {
        agent-on-claude = {
          harness = "claude";
          personality = "Claude harness agent";
        };
        agent-on-codex = {
          harness = "codex";
          personality = "Codex harness agent";
          modelByHarness.opencode = "opencode/some-free-model";
        };
        agent-on-discord = {
          harness = "claude";
          personality = "Discord channel agent";
          channel.type = "discord";
        };
        agent-on-discord-via-codex = {
          harness = "codex";
          personality = "Discord channel agent on codex";
          channel.type = "discord";
        };
      };
    }
  ];

  cfgWithBothHarnesses = helpers.homeManagerTestConfiguration bothHarnessModules;

  supervisedWindowsOfTheDefaultWorkspace =
    (builtins.head cfgWithBothHarnesses.clawde.serviceSpecification.sessions).agents;
in
{
  inherit
    bothHarnessModules
    cfgWithBothHarnesses
    supervisedWindowsOfTheDefaultWorkspace
    ;

  parseDeployedJson =
    deployedText: builtins.fromJSON (builtins.unsafeDiscardStringContext deployedText);

  supervisedWindowNames = map (window: window.name) supervisedWindowsOfTheDefaultWorkspace;

  sidecarProcessNamesOfAgent =
    agentName:
    map (sidecarProcess: sidecarProcess.name) (
      (builtins.head (
        builtins.filter (window: window.name == agentName) supervisedWindowsOfTheDefaultWorkspace
      )).sidecar_processes
    );
}
