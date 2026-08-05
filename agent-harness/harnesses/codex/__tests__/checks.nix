{
  helpers,
  pkgs,
  lib,
  inputs,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  interactiveAgentSkills =
    import
      ../../../../agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix
      {
        hostname = "test";
      };

  cfg =
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      extraSpecialArgs = {
        hostname = "test";
      };
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

  dotfilesAgentInstructions = builtins.readFile ../../../../agent-harness/agent-instructions/project-context/dotfiles-agent-instructions.md;
  normalizedDotfilesAgentInstructions = lib.replaceStrings [ "\n" ] [ " " ] dotfilesAgentInstructions;
  codexConfigSeedActivationData = cfg.home.activation.seedCodexConfigAsMutableFile.data or "";
  legacyCodexSkillDirectoriesScript = builtins.readFile ../scripts/replace-legacy-codex-skill-directories;
in
{
  codex-bin-wrapper =
    mkEvalCheck "codex-bin-wrapper" (builtins.hasAttr ".local/bin/codex" cfg.home.file)
      ".local/bin/codex should be in home.file";

  codex-skills-directory =
    mkEvalCheck "codex-skills-directory" (hasFilePrefix ".codex/skills/")
      "skills directory entries should be in home.file";

  codex-machine-tier-carries-the-shared-interactive-set =
    mkEvalCheck "codex-machine-tier-carries-the-shared-interactive-set"
      (builtins.all (
        skillName: builtins.hasAttr ".codex/skills/${skillName}" cfg.home.file
      ) interactiveAgentSkills.defaultInteractiveSkillNames)
      "every shared interactive skill must deploy into the Codex machine tier";

  codex-skills-only-deploy-complete-skills = mkEvalCheck "codex-skills-only-deploy-complete-skills" (
    !(builtins.hasAttr ".codex/skills/page-composer" cfg.home.file)
  ) "directories without SKILL.md should not be deployed as codex skills";

  codex-all-skills-index-skill =
    mkEvalCheck "codex-all-skills-index-skill"
      (builtins.hasAttr ".codex/skills/all-skills" cfg.home.file)
      "the generated all-skills index should be deployed for codex; research and every other non-curated skill stays reachable through it";

  codex-core-skill =
    mkEvalCheck "codex-core-skill" (builtins.hasAttr ".codex/skills/core" cfg.home.file)
      "core skill should be generated for codex";

  codex-replaces-legacy-generated-skill-directories =
    mkEvalCheck "codex-replaces-legacy-generated-skill-directories"
      (
        builtins.hasAttr "removeLegacyCodexSkillDirectories" cfg.home.activation
        && lib.hasInfix "replace-legacy-codex-skill-directories" cfg.home.activation.removeLegacyCodexSkillDirectories.data
      )
      "the generated core and all-skills directory links must replace their legacy leaf-symlink directories before Home Manager checks link targets";

  codex-removes-the-retired-pinchtab-skill =
    mkEvalCheck "codex-removes-the-retired-pinchtab-skill"
      (
        builtins.hasAttr "removeLegacyCodexSkillDirectories" cfg.home.activation
        && lib.hasInfix "pinchtab" legacyCodexSkillDirectoriesScript
      )
      "activation must remove the unmanaged PinchTab skill so browser remains the sole browser instruction surface";

  codex-global-agents-instructions =
    mkEvalCheck "codex-global-agents-instructions" (builtins.hasAttr ".codex/AGENTS.md" cfg.home.file)
      "core agent rules should be deployed as codex global ~/.codex/AGENTS.md instructions";

  codex-config-nix-source = mkEvalCheck "codex-config-nix-source" (
    builtins.hasAttr ".codex/config.toml.nix-source" cfg.home.file
    && !(builtins.hasAttr ".codex/config.toml" cfg.home.file)
  ) "Codex config must deploy an authoritative nix-source while leaving the live TOML mutable";

  codex-config-mutable-seed-activation = mkEvalCheck "codex-config-mutable-seed-activation" (
    builtins.hasAttr "seedCodexConfigAsMutableFile" cfg.home.activation
    && !(builtins.hasAttr "codexBaselineConfig" cfg.home.activation)
    && builtins.elem "linkGeneration" cfg.home.activation.seedCodexConfigAsMutableFile.after
    && lib.hasInfix "CODEX_TRUSTED_PROJECT_PARENT_DIRECTORIES" codexConfigSeedActivationData
    && lib.hasInfix "/home/test/repo" codexConfigSeedActivationData
  ) "Codex config must use Claude-style mutable seeding instead of the legacy generator activation";

  codex-config-legacy-profiles-removed = mkEvalCheck "codex-config-legacy-profiles-removed" (
    !(builtins.hasAttr ".codex/fast.config.toml" cfg.home.file)
    && !(builtins.hasAttr ".codex/deep.config.toml" cfg.home.file)
    && !(builtins.hasAttr ".codex/web.config.toml" cfg.home.file)
  ) "Codex-only generated profiles must stay removed";

  codex-config-agent-instructions-current =
    mkEvalCheck "codex-config-agent-instructions-current"
      (
        !(lib.hasInfix "codex config generator" normalizedDotfilesAgentInstructions)
        && !(lib.hasInfix "regenerated by merging into the existing file" normalizedDotfilesAgentInstructions)
        && lib.hasInfix "agent-harness/harnesses/claude-code/mcps/default.nix" normalizedDotfilesAgentInstructions
        && lib.hasInfix "agent-harness/harnesses/codex/config.nix" normalizedDotfilesAgentInstructions
        && lib.hasInfix "preserving live entries in projects, marketplaces, and plugins" normalizedDotfilesAgentInstructions
        && lib.hasInfix "sourced entries win on key collisions" normalizedDotfilesAgentInstructions
      )
      "Codex instructions must describe the current authoritative source and mutable seed ownership model";

  codex-claude-plugin-port-activation =
    mkEvalCheck "codex-claude-plugin-port-activation"
      (builtins.hasAttr "codexClaudePluginPort" cfg.home.activation)
      "enabled third-party Claude Code plugins should be ported into Codex via an activation step";

}
// import ./hook-registration-checks.nix {
  inherit
    pkgs
    lib
    mkEvalCheck
    cfg
    ;
}
