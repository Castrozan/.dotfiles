{
  helpers,
  pkgs,
  lib,
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
        inherit pkgs;
      };

  cfg = helpers.homeManagerTestConfigurationForEvaluatingSystem [ self.homeManagerModules.codex ];

  codexPackage = cfg.codex.unwrappedPackage;

  fileNames = builtins.attrNames cfg.home.file;

  hasFilePrefix =
    prefix: builtins.any (n: builtins.substring 0 (builtins.stringLength prefix) n == prefix) fileNames;

  dotfilesAgentInstructions = builtins.readFile ../../../../agent-harness/agent-instructions/project-context/dotfiles-agent-instructions.md;
  normalizedDotfilesAgentInstructions = lib.replaceStrings [ "\n" ] [ " " ] dotfilesAgentInstructions;
  codexConfigSeedActivationData = cfg.home.activation.seedCodexConfigAsMutableFile.data or "";
  codexConfigModule = builtins.readFile ../config.nix;
in
{
  codex-bin-wrapper =
    mkEvalCheck "codex-bin-wrapper" (builtins.hasAttr ".local/bin/codex" cfg.home.file)
      ".local/bin/codex should be in home.file";

  codex-interactive-profile =
    pkgs.runCommand "check-codex-interactive-profile" { nativeBuildInputs = [ pkgs.python312 ]; }
      ''
        python - ${cfg.home.file.".codex/dotfiles-interactive.config.toml.nix-source".source} <<'PY'
        from pathlib import Path
        import sys
        import tomllib
        configuration = tomllib.loads(Path(sys.argv[1]).read_text())
        assert set(configuration) == {"developer_instructions"}
        assert "### Interactive session" in configuration["developer_instructions"]
        assert "### Servant" in configuration["developer_instructions"]
        PY
        touch "$out"
      '';

  codex-profiles-are-mutable = mkEvalCheck "codex-profiles-are-mutable" (
    !(builtins.hasAttr ".codex/dotfiles-interactive.config.toml" cfg.home.file)
    && builtins.elem "linkGeneration" cfg.home.activation.seedCodexProfilesAsMutableFiles.after
  ) "Codex must seed writable profiles after removing the previous generation's symlinks";

  codex-package-uses-upstream-binaries =
    assert lib.assertMsg
      (!(codexPackage.drvAttrs ? cargoDeps) && (codexPackage.drvAttrs.patches or [ ]) == [ ])
      "Codex must use unpatched upstream prebuilt binaries; see agent-harness/harnesses/codex/README.md";
    pkgs.runCommand "check-codex-package-uses-upstream-binaries" { } ''
      export HOME="$TMPDIR"
      codexExecutable=${lib.getExe codexPackage}
      codexExecutableDirectory=$(dirname "$(readlink -f "$codexExecutable")")
      test "$codexExecutableDirectory" = "$(dirname "$codexExecutable")"
      test -x "$codexExecutableDirectory/codex-code-mode-host"
      test -f "$codexExecutableDirectory/../codex-package.json"
      test -x "$codexExecutableDirectory/../codex-path/rg"
      "$codexExecutable" --version >/dev/null 2>&1
      "$codexExecutableDirectory/codex-code-mode-host" --help >/dev/null
      touch "$out"
    '';

  codex-daemon-is-declarative = mkEvalCheck "codex-daemon-is-declarative" (
    let
      settings = builtins.fromJSON cfg.home.file.".codex/app-server-daemon/settings.json".text;
    in
    toString cfg.home.file.".codex/packages/app-server-daemon/current".source == "${codexPackage}"
    && !settings.remoteControlEnabled
    && !settings.updater.autoUpdateEnabled
  ) "Codex must select its Nix package and disable independent updates and remote control";

  codex-production-plugin-registration =
    mkEvalCheck "codex-production-plugin-registration"
      (
        builtins.hasAttr "installProductionCodexPlugin" cfg.home.activation
        && builtins.hasAttr ".local/share/agent-plugins/dotfiles" cfg.home.file
        && !(hasFilePrefix ".codex/skills/")
      )
      "Codex must register the complete production package without duplicate managed global skill projections";

  codex-global-agents-instructions =
    mkEvalCheck "codex-global-agents-instructions" (builtins.hasAttr ".codex/AGENTS.md" cfg.home.file)
      "core agent rules should be deployed as codex global ~/.codex/AGENTS.md instructions";

  codex-config-nix-source = mkEvalCheck "codex-config-nix-source" (
    builtins.hasAttr ".codex/config.toml.nix-source" cfg.home.file
    && !(builtins.hasAttr ".codex/config.toml" cfg.home.file)
  ) "Codex config must deploy an authoritative nix-source while leaving the live TOML mutable";

  codex-config-preserves-terminal-scrollback =
    pkgs.runCommand "check-codex-config-preserves-terminal-scrollback"
      { nativeBuildInputs = [ pkgs.python312 ]; }
      ''
        python - ${cfg.home.file.".codex/config.toml.nix-source".source} <<'PY'
        from pathlib import Path
        import sys
        import tomllib
        configuration = tomllib.loads(Path(sys.argv[1]).read_text())
        assert configuration["tui"]["alternate_screen"] == "never"
        PY
        touch "$out"
      '';

  codex-config-leaves-model-runtime-owned =
    mkEvalCheck "codex-config-leaves-model-runtime-owned" (!(lib.hasInfix "model = " codexConfigModule))
      "Codex model selection must remain runtime-owned so a rebuild preserves the user's remembered model";

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
        && lib.hasInfix "The live model and entries in projects, marketplaces, and plugins survive rebuilds" normalizedDotfilesAgentInstructions
        && lib.hasInfix "declarative source wins every other key collision" normalizedDotfilesAgentInstructions
      )
      "Codex instructions must describe the current authoritative source and mutable seed ownership model";

  codex-retired-plugin-port = mkEvalCheck "codex-retired-plugin-port" (
    !(builtins.hasAttr "codexClaudePluginPort" cfg.home.activation)
  ) "Codex must retain native complete packages without the retired skill-only Claude copier";

}
// import ./hook-registration-checks.nix {
  inherit
    pkgs
    lib
    mkEvalCheck
    cfg
    ;
}
