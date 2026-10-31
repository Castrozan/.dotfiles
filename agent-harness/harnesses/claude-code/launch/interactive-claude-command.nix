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

  claudeModsMarketplace = import ../plugins/mods/marketplace.nix { inherit pkgs; };

  interactiveSessionSettings = {
    enabledPlugins = claudeModsMarketplace.interactiveSessionEnabledPlugins;
    pluginConfigs = claudeModsMarketplace.interactiveSessionPluginConfigs;
  };

  interactiveSessionSettingsFile = pkgs.writeText "claude-interactive-session-settings.json" (
    builtins.toJSON interactiveSessionSettings
  );

  workspaceProfileActivation = import ./workspace-profile-settings-and-instructions.nix {
    inherit
      pkgs
      lib
      interactiveSessionOnlySystemPromptSurfaces
      interactiveSessionSettings
      ;
  };

  inherit (import ../../../workspace-profiles/activation/harness-launch-dispatch.nix { inherit lib; })
    mkWorkspaceProfileLaunchDispatch
    ;

  workspaceProfileLaunchDispatch = mkWorkspaceProfileLaunchDispatch {
    inherit (config) agentWorkspaceProfiles;
    inherit (workspaceProfileActivation) activationShellStatementsForProfile;
  };

  # No servant wiring here on purpose. The Servant is derived at SessionStart from
  # the id Claude Code mints for itself, so this wrapper neither knows nor needs to
  # know which one a launch draws, and a resume lands on the same one for free.
  claudePackage = pkgs.writeShellScriptBin "claude" ''
    claudeSystemPromptFile="${interactiveSessionOnlySystemPromptSurfaces}"
    claudeSettingsFile="${interactiveSessionSettingsFile}"
    resolvedWorkspaceProfileName=""
    ${workspaceProfileLaunchDispatch}
    export AGENT_INTERACTIVE_PREFERENCES_PATH="$claudeSystemPromptFile"
    case "''${1-}" in
      remote-control | rc | remote | sync | bridge)
        exec ${claudeExecutable} "$@"
        ;;
    esac
    exec ${claudeExecutable} \
      --dangerously-skip-permissions \
      --append-system-prompt-file "$claudeSystemPromptFile" \
      --settings "$claudeSettingsFile" \
      "$@"
  '';
in
{
  options.claude = {
    package = lib.mkOption {
      type = lib.types.package;
      default = claudePackage;
      readOnly = true;
      description = "The package exposed as the plain claude command, carrying the interactive prompt and workspace profile.";
    };

    interactiveSessionSettings = lib.mkOption {
      type = lib.types.attrsOf lib.types.anything;
      default = interactiveSessionSettings;
      readOnly = true;
      description = "The settings the plain claude command layers onto every interactive session before any workspace profile overlay, for a non-interactive launcher that must give its sessions the same plugins and plugin options.";
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
