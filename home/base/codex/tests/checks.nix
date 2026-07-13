{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg =
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      modules = [
        self.homeManagerModules.codex
        {
          home = {
            username = "test";
            homeDirectory = "/home/test";
            inherit (helpers) stateVersion;
          };
        }
      ];
    }).config;

  fileNames = builtins.attrNames cfg.home.file;

  hasFilePrefix =
    prefix: builtins.any (n: builtins.substring 0 (builtins.stringLength prefix) n == prefix) fileNames;
in
{
  codex-bin-wrapper =
    mkEvalCheck "codex-bin-wrapper" (builtins.hasAttr ".local/bin/codex" cfg.home.file)
      ".local/bin/codex should be in home.file";

  codex-skills-directory =
    mkEvalCheck "codex-skills-directory" (hasFilePrefix ".codex/skills/")
      "skills directory entries should be in home.file";

  codex-skills-only-deploy-complete-skills = mkEvalCheck "codex-skills-only-deploy-complete-skills" (
    !(builtins.hasAttr ".codex/skills/page-composer" cfg.home.file)
  ) "directories without SKILL.md should not be deployed as codex skills";

  codex-research-skill =
    mkEvalCheck "codex-research-skill" (builtins.hasAttr ".codex/skills/research" cfg.home.file)
      "research skill should be deployed for codex";

  codex-core-skill =
    mkEvalCheck "codex-core-skill" (builtins.hasAttr ".codex/skills/core/SKILL.md" cfg.home.file)
      "core skill should be generated for codex";

  codex-global-agents-instructions =
    mkEvalCheck "codex-global-agents-instructions" (builtins.hasAttr ".codex/AGENTS.md" cfg.home.file)
      "core agent rules should be deployed as codex global ~/.codex/AGENTS.md instructions";

  codex-claude-plugin-port-activation =
    mkEvalCheck "codex-claude-plugin-port-activation"
      (builtins.hasAttr "codexClaudePluginPort" cfg.home.activation)
      "third-party Claude Code plugins should be ported into Codex via an activation step";

  codex-hooks-config-managed-file =
    mkEvalCheck "codex-hooks-config-managed-file" (builtins.hasAttr ".codex/hooks.json" cfg.home.file)
      "Codex hooks should be deployed as a declarative home.file entry";

  codex-hooks-config-current-schema =
    let
      hooksFile = cfg.home.file.".codex/hooks.json" or null;
      hooksConfig =
        if hooksFile != null && hooksFile ? text then builtins.fromJSON hooksFile.text else { };
      sessionStartGroups =
        if hooksConfig ? hooks && hooksConfig.hooks ? SessionStart then
          hooksConfig.hooks.SessionStart
        else
          [ ];
      firstSessionStartGroup =
        if sessionStartGroups == [ ] then { } else builtins.head sessionStartGroups;
    in
    mkEvalCheck "codex-hooks-config-current-schema" (
      hooksConfig ? hooks && firstSessionStartGroup ? hooks
    ) "Codex hooks.json should use the current top-level hooks schema";
}
