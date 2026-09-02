{
  pkgs,
  lib,
  hostname,
  isDarwin ? false,
  ...
}:
let
  hooksConfig =
    import
      ../../../../agent-harness/hooks/integrations/claude/event-registrations/claude-hook-event-registrations.nix
      { inherit lib hostname isDarwin; };
  pluginsConfig = import ./plugins.nix { inherit pkgs; };

  privateMarketplacePluginsPath =
    ../../../../private-configuration/machines + "/${hostname}/claude-plugins.nix";
  privateMarketplacePlugins =
    if builtins.pathExists privateMarketplacePluginsPath then
      import privateMarketplacePluginsPath
    else
      { };

  claudeKeybindings = {
    "$schema" = "https://www.schemastore.org/claude-code-keybindings.json";
    "$docs" = "https://code.claude.com/docs/en/keybindings";
    bindings = [
      {
        context = "Chat";
        bindings = {
          "ctrl+e" = "chat:undo";
        };
      }
    ];
  };

  spinnerVerbs = import ./spinner-verbs.nix;

  defaultModelByHostname = {
    kira = "claude-fable-5-1";
  };
  defaultModelForThisHost = defaultModelByHostname.${hostname} or "claude-sonnet-5";

  claudeGlobalSettings = {
    model = defaultModelForThisHost;
    effortLevel = "max";
    ultracode = false;
    enableWorkflows = true;
    language = "english";
    animationInterval = 80;
    spinnerText = spinnerVerbs;
    spinnerTipsEnabled = false;
    spinnerVerbs = {
      mode = "replace";
      verbs = spinnerVerbs;
    };
    dangerouslySkipPermissions = true;
    skipDangerousModePermissionPrompt = true;
    includeCoAuthoredBy = false;
    includeGitInstructions = false;
    cleanupPeriodDays = 3650;
    showTurnDuration = true;
    awaySummaryEnabled = true;
    teammateMode = "tmux";
    permissions = {
      defaultMode = "bypassPermissions";
      allow = [ ];
      deny = [ "Artifact" ];
    };
    terminalShowHoverHint = false;
    statusLine = {
      type = "command";
      command = "bash $HOME/.claude/statusline-command.sh";
    };
    composer = {
      shouldChimeAfterChatFinishes = true;
    };
    fileFiltering = {
      respectGitignore = true;
    };
    hooks = hooksConfig;
  }
  // privateMarketplacePlugins;

  claudeGlobalSettingsJson = builtins.toJSON claudeGlobalSettings;

  claudeGlobalRules = builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/core.md;
in
{
  imports = [
    ./workarounds
  ];

  home = {
    inherit (pluginsConfig) packages;

    file = {
      ".claude/.keep".text = "";
      ".claude/statusline-command.sh".source = ./statusline/statusline-command.sh;
      ".claude/statusline-command-git-segment.sh".source = ./statusline/statusline-command-git-segment.sh;
      ".claude/statusline-command-json-segments.sh".source =
        ./statusline/statusline-command-json-segments.sh;
      ".claude/settings.json.nix-source".text = claudeGlobalSettingsJson;
      ".claude/keybindings.json".text = builtins.toJSON claudeKeybindings;
      ".claude/CLAUDE.md".text = claudeGlobalRules;
    };
  };
}
