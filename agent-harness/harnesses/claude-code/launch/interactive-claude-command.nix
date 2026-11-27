{
  config,
  lib,
  pkgs,
  ...
}:
let
  interactiveSessionOnlySystemPromptSurfaces = import ./interactive-session-instructions.nix {
    inherit pkgs;
    inherit (config.home) homeDirectory;
  };

  claudeExecutable = lib.getExe config.claude.unwrappedPackage;

  claudeMods = import ../plugins/mods { inherit pkgs; };

  interactiveSessionSettings = {
    pluginConfigs = claudeMods.interactiveSessionPluginConfigs;
  };

  interactiveSessionSettingsFile = pkgs.writeText "claude-interactive-session-settings.json" (
    builtins.toJSON interactiveSessionSettings
  );

  # No servant wiring here on purpose. The Servant is derived at SessionStart from
  # the id Claude Code mints for itself, so this wrapper neither knows nor needs to
  # know which one a launch draws, and a resume lands on the same one for free.
  claudePackage = pkgs.writeShellApplication {
    name = "claude";
    bashOptions = [ ];
    runtimeEnv = {
      CLAUDE_LAUNCHER_BINARY = claudeExecutable;
      CLAUDE_LAUNCHER_SYSTEM_PROMPT_FILE = "${interactiveSessionOnlySystemPromptSurfaces}";
      CLAUDE_LAUNCHER_SETTINGS_FILE = "${interactiveSessionSettingsFile}";
      CLAUDE_LAUNCHER_PLUGIN_DIRECTORY = "${claudeMods.interactiveSessionModsDirectory}";
    };
    text = builtins.readFile ../scripts/launch-interactive-claude.sh;
  };
in
{
  options.claude = {
    package = lib.mkOption {
      type = lib.types.package;
      default = claudePackage;
      readOnly = true;
      description = "The package exposed as the plain claude command, carrying the interactive prompt and mods.";
    };

    interactiveSessionSettings = lib.mkOption {
      type = lib.types.attrsOf lib.types.anything;
      default = interactiveSessionSettings;
      readOnly = true;
      description = "The settings the plain claude command layers onto every interactive session, including interactive mod options.";
    };

    interactiveSessionModsDirectory = lib.mkOption {
      type = lib.types.path;
      default = claudeMods.interactiveSessionModsDirectory;
      readOnly = true;
      description = "The directory of mods the plain claude command loads with --plugin-dir, for a non-interactive launcher that must give its sessions the same mods.";
    };

    interactiveSessionSystemPromptFile = lib.mkOption {
      type = lib.types.path;
      default = interactiveSessionOnlySystemPromptSurfaces;
      readOnly = true;
      description = "The system prompt file the plain claude command appends and exports as the interactive session marker, for a non-interactive launcher whose sessions a human drives.";
    };

  };

  config.home = {
    packages = [ claudePackage ];
    activation.removeDanglingClaudeBackup = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
      claudeBackup="${config.home.homeDirectory}/.local/bin/claude.bak"
      if [ -L "$claudeBackup" ] && [ ! -e "$claudeBackup" ]; then
        run ${pkgs.coreutils}/bin/rm -- "$claudeBackup"
      fi
    '';
    file.".local/bin/claude" = {
      source = "${claudePackage}/bin/claude";
      force = true;
    };
  };
}
