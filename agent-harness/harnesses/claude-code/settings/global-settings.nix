{
  pkgs,
  lib,
  config,
  hostname,
  ...
}:
let
  pluginsConfig = import ../plugins/language-server-packages.nix { inherit pkgs; };

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

  claudeGlobalSettings = {
    ultracode = false;
    enableWorkflows = true;
    language = "english";
    animationInterval = 80;
    spinnerText = spinnerVerbs;
    spinnerTipsEnabled = false;
    feedbackDrafts = "off";
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
    deniedMcpServers = [
      { serverName = "plugin:betha-desenvolvimento:chrome-devtools"; }
      { serverName = "plugin:betha-chrome-devtools:chrome-devtools"; }
    ];
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
    hooks = {
      SessionStart = [
        {
          matcher = "*";
          hooks = [
            {
              type = "command";
              command = "bash ${lib.escapeShellArg "${config.home.homeDirectory}/.claude/hooks/herdr-agent-state.sh"} session";
              timeout = 10;
            }
          ];
        }
      ];
    };
  }
  // privateMarketplacePlugins;

  baseSettings = pkgs.writeText "claude-base-settings.json" (builtins.toJSON claudeGlobalSettings);
  claudeGlobalSettingsJson =
    pkgs.runCommand "claude-settings.json"
      {
        nativeBuildInputs = [ pkgs.jq ];
        passthru = { inherit baseSettings; };
      }
      ''
        jq -s '.[0] as $base | .[1] as $generated | $base * $generated |
          .hooks.SessionStart = ($generated.hooks.SessionStart + $base.hooks.SessionStart)' \
          ${baseSettings} ${config.agentPlugins.bundle}/plugin/native/claude/hooks.json > "$out"
      '';

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
      ".claude/settings.json.nix-source".source = claudeGlobalSettingsJson;
      ".claude/keybindings.json".text = builtins.toJSON claudeKeybindings;
      ".claude/CLAUDE.md".source = "${config.agentPlugins.bundle}/plugin/native/claude/CLAUDE.md";
    };
  };
}
