{
  pkgs,
  lib,
  hostname,
  ...
}:
let
  hooksConfig = import ../hooks/event-registrations.nix { inherit lib hostname; };
  pluginsConfig = import ./plugins.nix { inherit pkgs; };

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

  claudeGlobalSettings = {
    model = "claude-opus-4-8";
    effortLevel = "max";
    ultracode = true;
    enableWorkflows = true;
    language = "english";
    spinnerTipsEnabled = false;
    dangerouslySkipPermissions = true;
    skipDangerousModePermissionPrompt = true;
    includeCoAuthoredBy = false;
    includeGitInstructions = false;
    showTurnDuration = true;
    teammateMode = "tmux";
    permissions = {
      defaultMode = "bypassPermissions";
      allow = [ ];
      deny = [ ];
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
    enabledPlugins = {
      "discord@claude-plugins-official" = true;
    };
  };

  claudeGlobalSettingsJson = builtins.toJSON claudeGlobalSettings;

  coreAgentRawContent = builtins.readFile ../../../../agents/core_rules/core.md;
  coreAgentSplitOnFrontmatterDelimiter = builtins.split "---\n" coreAgentRawContent;
  coreAgentBodyWithoutFrontmatter = builtins.elemAt coreAgentSplitOnFrontmatterDelimiter 4;

  claudeGlobalRules = coreAgentBodyWithoutFrontmatter;
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
