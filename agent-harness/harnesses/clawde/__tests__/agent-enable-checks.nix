{
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ./harness-check-fixtures.nix { inherit helpers self; };

  cfgWithADisabledAgent = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    {
      clawde.agents = {
        off-agent = {
          enable = false;
          harness = "claude";
          personality = "Discord agent switched off but still declared";
          channel.type = "discord";
        };
        on-agent = {
          harness = "claude";
          personality = "Discord agent left on by the default";
          channel.type = "discord";
        };
      };
    }
  ];

  supervisedWindowNames = map (
    window: window.name
  ) (builtins.head cfgWithADisabledAgent.clawde.serviceSpecification.sessions).agents;
in
{
  clawde-a-disabled-agent-leaves-the-agent-set-its-declaration-stays-in =
    mkEvalCheck "clawde-a-disabled-agent-leaves-the-agent-set-its-declaration-stays-in"
      (!(cfgWithADisabledAgent.clawde.agents ? off-agent))
      "enable = false is the off switch that keeps the config: the declaration stays in the tree, but the agent must vanish from config.clawde.agents before the clawde module reads it, because every consumer, the supervisor spec, the health probes, the a2a card and the channel adapter, iterates that set and would otherwise keep the agent alive";

  clawde-a-disabled-agent-gets-no-supervised-window =
    mkEvalCheck "clawde-a-disabled-agent-gets-no-supervised-window"
      (!(builtins.elem "off-agent" supervisedWindowNames))
      "a disabled discord agent must hold nothing: no window means no wrapper, no heartbeat and no sidecar bridge, which is what separates enable = false from onDemand, whose service-lifetime bridge stays connected so a message can start the agent";

  clawde-an-agent-is-enabled-by-default =
    mkEvalCheck "clawde-an-agent-is-enabled-by-default"
      ((cfgWithADisabledAgent.clawde.agents ? on-agent) && builtins.elem "on-agent" supervisedWindowNames)
      "every agent already declared across the fleet says nothing about enable, so the default must keep them all live; a false default would silently empty the fleet on the next rebuild";

  clawde-an-enabled-agent-keeps-the-harness-fixtures-intact =
    mkEvalCheck "clawde-an-enabled-agent-keeps-the-harness-fixtures-intact"
      (builtins.all (name: builtins.elem name fixtures.supervisedWindowNames) [
        "agent-on-claude"
        "agent-on-codex"
        "agent-on-discord"
      ])
      "the filter is applied to the whole agent set, so a mistake in it would drop enabled agents too; the shared harness fixtures declare no enable and must all still reach the supervisor spec";
}
