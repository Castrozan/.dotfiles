{
  pkgs,
  lib,
  inputs,
  self,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix { inherit pkgs lib inputs; };
  inherit (helpers) mkEvalCheck;

  minimalCfg =
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      modules = [
        self.homeManagerModules.openclaw
        {
          home.username = "test";
          home.homeDirectory = "/home/test";
          home.stateVersion = "25.11";
        }
      ];
    }).config;

  withAgentCfg =
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      modules = [
        self.homeManagerModules.openclaw
        {
          home.username = "test";
          home.homeDirectory = "/home/test";
          home.stateVersion = "25.11";
          openclaw.agents.eval-bot = {
            enable = true;
            workspace = "openclaw/eval-bot";
          };
        }
      ];
    }).config;
in
{
  openclaw-config-namespace-exists =
    mkEvalCheck "openclaw-config-namespace-exists" (builtins.hasAttr "agents" minimalCfg.openclaw)
      "openclaw config option namespace should exist";

  openclaw-agents-submodule-type =
    mkEvalCheck "openclaw-agents-submodule-type"
      (builtins.hasAttr "eval-bot" withAgentCfg.openclaw.agents)
      "agents attr should accept submodule type";

  openclaw-agent-config-evaluates =
    mkEvalCheck "openclaw-agent-config-evaluates"
      (
        withAgentCfg.openclaw.agents.eval-bot.enable == true
        && withAgentCfg.openclaw.defaultAgent == "eval-bot"
      )
      "agent config should evaluate with test agent, defaultAgent=${withAgentCfg.openclaw.defaultAgent}";
}
