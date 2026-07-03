{
  pkgs,
  lib,
  hostname,
  ...
}: let
  hooksConfig = import ../hooks/event-registrations {inherit lib hostname;};
  pluginsConfig = import ./plugins.nix {inherit pkgs;};

  privateMarketplacePluginsPath =
    ../../../../private-config/machines + "/${hostname}/claude-plugins.nix";
  privateMarketplacePlugins =
    if builtins.pathExists privateMarketplacePluginsPath
    then import privateMarketplacePluginsPath
    else {};

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

  spinnerVerbs = [
    "Chudmaxxing"
    "Aura-farming"
    "Redeeming"
    "Clodding"
    "Tokenmaxxing"
    "Slopping"
    "Clanking"
    "Ignoring GPL"
    "Increasing ram prices"
    "Hallucinating"
    "Selling your data"
    "Outsourcing to Mossad"
    "Gemming it up"
    "Absolute coaling"
    "Truth-nuking"
    "Fakecelling"
    "Truecelling"
    "Mogging"
    "Rizzing"
    "Dumbing it down"
    "Enshittifying"
    "Going full retard"
    "Summoning Cheesy Micheal"
    "Degenerating"
    "Running \"sudo rm -rf --no-preserve-root /\""
    "Virtual insanitying"
    "Bomboclating"
    "Gambling"
    "Ending it all"
    "Rebooting"
    "Unicycling"
    "Horsing around"
    "Calling Mahoraga"
    "Calling Kevin"
    "Calling Saul"
    "Nuking SF"
    "Spellcasting"
    "Hexing"
    "Prompt-injecting"
    "Installing Windows"
    "Ultrathinking"
    "Nuking prod"
    "Tokenmining"
    "Questioning"
    "Chinesing"
    "Selling the wife and kids"
    "Increasing shareholder value"
    "Winging it"
    "Cooking"
  ];

  claudeGlobalSettings =
    {
      model = "claude-opus-4-8[1m]";
      effortLevel = "max";
      ultracode = true;
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
      showTurnDuration = true;
      teammateMode = "tmux";
      permissions = {
        defaultMode = "bypassPermissions";
        allow = [];
        deny = [];
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

  coreAgentRawContent = builtins.readFile ../../../../agents/core_rules/core.md;
  coreAgentSplitOnFrontmatterDelimiter = builtins.split "---\n" coreAgentRawContent;
  coreAgentBodyWithoutFrontmatter = builtins.elemAt coreAgentSplitOnFrontmatterDelimiter 4;

  claudeGlobalRules = coreAgentBodyWithoutFrontmatter;
in {
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
