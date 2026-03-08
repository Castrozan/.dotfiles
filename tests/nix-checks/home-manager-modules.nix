{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ./helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  mkModuleConfig =
    moduleName:
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      modules = [
        self.homeManagerModules.${moduleName}
        {
          home.username = "test";
          home.homeDirectory = "/home/test";
          home.stateVersion = helpers.stateVersion;
        }
      ];
    }).config;

  mkModuleConfigWithAgents =
    moduleName:
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      modules = [
        self.homeManagerModules.${moduleName}
        {
          home.username = "test";
          home.homeDirectory = "/home/test";
          home.stateVersion = helpers.stateVersion;
          openclaw.agents.eval-bot = {
            enable = true;
            workspace = "openclaw/eval-bot";
          };
        }
      ];
    }).config;

  openclawCfg = mkModuleConfig "openclaw";
  claudeCfg = mkModuleConfig "claude-code";
  codexCfg = mkModuleConfig "codex";
  defaultCfg = mkModuleConfig "default";
  defaultWithAgentsCfg = mkModuleConfigWithAgents "default";
in
{
  hm-module-openclaw-evaluates =
    mkEvalCheck "hm-module-openclaw-evaluates" (builtins.hasAttr "openclaw" openclawCfg)
      "openclaw module should evaluate and expose openclaw config";

  hm-module-claude-code-evaluates =
    mkEvalCheck "hm-module-claude-code-evaluates"
      (builtins.hasAttr ".claude/settings.json" claudeCfg.home.file)
      "claude-code module should produce .claude/settings.json";

  hm-module-codex-evaluates =
    mkEvalCheck "hm-module-codex-evaluates" (builtins.hasAttr ".local/bin/codex" codexCfg.home.file)
      "codex module should produce .local/bin/codex";

  hm-module-default-combines-all = mkEvalCheck "hm-module-default-combines-all" (
    builtins.hasAttr "openclaw" defaultCfg
    && builtins.hasAttr ".claude/settings.json" defaultCfg.home.file
    && builtins.hasAttr ".local/bin/codex" defaultCfg.home.file
  ) "default module should combine openclaw + claude + codex";

  hm-module-default-all-files = mkEvalCheck "hm-module-default-all-files" (
    builtins.hasAttr "openclaw" defaultWithAgentsCfg
    && builtins.hasAttr ".claude/settings.json" defaultWithAgentsCfg.home.file
    && builtins.hasAttr ".claude/mcp.json" defaultWithAgentsCfg.home.file
    && builtins.hasAttr ".local/bin/claude" defaultWithAgentsCfg.home.file
    && builtins.hasAttr ".local/bin/codex" defaultWithAgentsCfg.home.file
  ) "default module should have openclaw options + claude files + codex files";
}
