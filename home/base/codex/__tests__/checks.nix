{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
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

  parsedCodexHooksConfig = {
    hooks = import ../hooks/configuration.nix {
      inherit pkgs lib;
      hostname = "test";
    };
  };
  codexSystemManagedHooksConfig = import ../system-managed-hooks.nix {
    inherit pkgs lib;
    hostname = "test";
  };
  darwinConfigurationsSource = builtins.readFile ../../../../flake/darwin-configurations.nix;
  nixosConfigurationsSource = builtins.readFile ../../../../flake/nixos-configurations.nix;

  codexSessionStartGroups =
    if parsedCodexHooksConfig ? hooks && parsedCodexHooksConfig.hooks ? SessionStart then
      parsedCodexHooksConfig.hooks.SessionStart
    else
      [ ];
  firstCodexSessionStartGroup =
    if codexSessionStartGroups == [ ] then { } else builtins.head codexSessionStartGroups;

  dotfilesAgentInstructions = builtins.readFile ../../../../agents/dotfiles.md;
  normalizedDotfilesAgentInstructions = lib.replaceStrings [ "\n" ] [ " " ] dotfilesAgentInstructions;
  codexConfigSeedActivationData = cfg.home.activation.seedCodexConfigAsMutableFile.data or "";

  codexHookEventCommands =
    eventName:
    let
      eventGroups =
        if parsedCodexHooksConfig ? hooks && parsedCodexHooksConfig.hooks ? ${eventName} then
          parsedCodexHooksConfig.hooks.${eventName}
        else
          [ ];
    in
    builtins.concatMap (group: map (hook: hook.command or "") (group.hooks or [ ])) eventGroups;

  codexHookEventRunsScript =
    eventName: scriptName:
    builtins.any (command: lib.hasInfix scriptName command) (codexHookEventCommands eventName);

  codexEventsRegisteringMoreThanOneCommand = lib.filter (
    eventName: lib.length (codexHookEventCommands eventName) > 1
  ) (lib.attrNames (parsedCodexHooksConfig.hooks or { }));
in
{
  codex-hooks-every-event-registers-exactly-one-command =
    mkEvalCheck "codex-hooks-every-event-registers-exactly-one-command"
      (codexEventsRegisteringMoreThanOneCommand == [ ])
      "every Codex hook event must register exactly one command, the same invariant settings.json carries on the Claude side. A second registration on the same event is a second interpreter per matching tool call and splits the decision across processes whose ordering and precedence nothing arbitrates. Events currently registering more than one command: ${lib.concatStringsSep ", " codexEventsRegisteringMoreThanOneCommand}. Fold the extra registration into that event's dispatcher and gate it with a handler tool_matcher";

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
        && lib.hasInfix "home/base/claude/mcps/default.nix" normalizedDotfilesAgentInstructions
        && lib.hasInfix "home/base/codex/config.nix" normalizedDotfilesAgentInstructions
        && lib.hasInfix "preserving live entries in projects, marketplaces, and plugins" normalizedDotfilesAgentInstructions
        && lib.hasInfix "sourced entries win on key collisions" normalizedDotfilesAgentInstructions
      )
      "Codex instructions must describe the current authoritative source and mutable seed ownership model";

  codex-claude-plugin-port-activation =
    mkEvalCheck "codex-claude-plugin-port-activation"
      (builtins.hasAttr "codexClaudePluginPort" cfg.home.activation)
      "enabled third-party Claude Code plugins should be ported into Codex via an activation step";

  codex-hooks-config-managed-file =
    mkEvalCheck "codex-hooks-config-managed-file"
      (
        !(builtins.hasAttr ".codex/hooks.json" cfg.home.file)
        && builtins.hasAttr "codex/requirements.toml" codexSystemManagedHooksConfig.environment.etc
        && lib.hasInfix "../home/base/codex/system-managed-hooks.nix" darwinConfigurationsSource
        && lib.hasInfix "../home/base/codex/system-managed-hooks.nix" nixosConfigurationsSource
      )
      "Codex hooks should be deployed through /etc/codex/requirements.toml on Darwin and NixOS so Codex treats them as managed and trusted";

  codex-hooks-config-current-schema = mkEvalCheck "codex-hooks-config-current-schema" (
    parsedCodexHooksConfig ? hooks && firstCodexSessionStartGroup ? hooks
  ) "Codex managed requirements should use the current top-level hooks schema";

  codex-hooks-config-session-start-compaction-only =
    mkEvalCheck "codex-hooks-config-session-start-compaction-only"
      ((firstCodexSessionStartGroup.matcher or "") == "compact")
      "Codex SessionStart should run only after compaction, not on startup, resume, or clear";

  codex-hooks-config-post-tool-use-dispatcher =
    mkEvalCheck "codex-hooks-config-post-tool-use-dispatcher"
      (codexHookEventRunsScript "PostToolUse" "post-tool-use-dispatcher.py")
      "Codex PostToolUse must run the same post-tool-use-dispatcher.py Claude registers; it composes auto-format, record-edited-source-file and nix-rebuild-trigger, and test_codex_surface_handler_composition guards that those three stay on the codex surface";

  codex-hooks-config-pre-tool-use-dispatcher =
    mkEvalCheck "codex-hooks-config-pre-tool-use-dispatcher"
      (codexHookEventRunsScript "PreToolUse" "pre-tool-use-dispatcher.py")
      "Codex PreToolUse must run the same pre-tool-use-dispatcher.py Claude registers (env-prefixed with the per-host PROHIBITED_WORDS_ALLOWED allowlist); it composes memory-recall and the prohibited-command/word guards, and test_codex_surface_handler_composition guards that those three stay on the codex surface";

  codex-hooks-config-stop-dispatcher =
    mkEvalCheck "codex-hooks-config-stop-dispatcher"
      (codexHookEventRunsScript "Stop" "stop-dispatcher.py")
      "Codex Stop must run the same stop-dispatcher.py Claude registers; it composes lint-turn-review on both surfaces and end-of-turn-format-guard on Claude only";

  codex-hooks-every-dispatcher-declares-its-surface =
    let
      dispatcherCommands = lib.filter (command: lib.hasInfix "-dispatcher.py" command) (
        lib.concatMap codexHookEventCommands (lib.attrNames (parsedCodexHooksConfig.hooks or { }))
      );
    in
    mkEvalCheck "codex-hooks-every-dispatcher-declares-its-surface"
      (
        dispatcherCommands != [ ]
        && lib.all (command: lib.hasInfix "--surface=codex" command) dispatcherCommands
      )
      "every Codex dispatcher registration must pass --surface=codex explicitly; the dispatchers default to the claude surface, so a registration that omits the flag silently runs Claude-only handlers (the reply-shape gate, the background-bash validator, the workspace injector) against a Codex session";
}
