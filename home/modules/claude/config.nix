{ pkgs, ... }:
let
  claudeGlobalSettings = {
    model = "opus";
    spinnerTipsEnabled = false;
    dangerouslySkipPermissions = true;
    permissions = {
      defaultMode = "bypassPermissions";
      allow = [ "*" ];
      deny = [ ];
    };
    terminalShowHoverHint = false;
    composer = {
      shouldChimeAfterChatFinishes = true;
    };
    agent = {
      permissionMode = "allow-all";
      disallowedTools = [ ];
    };
  };

  claudeDotfilesRules = ''
    # Claude Code Project Context

    ${builtins.readFile ../../../agents/rules/ai-interaction-guidelines.md}

    ${builtins.readFile ../../../agents/rules/gnome-keybinding-debugging.md}
  '';
in
{
  home.file.".claude/.keep".text = "";
  home.file.".claude/settings.json".text = builtins.toJSON claudeGlobalSettings;
  home.file.".dotfiles/CLAUDE.md".text = claudeDotfilesRules; # add symlink to dotfiles for easy reference

  home.sessionVariables = {
    CLAUDE_CODE_SHELL = "${pkgs.bash}/bin/bash";
    CLAUDE_BASH_NO_LOGIN = "1";
    BASH_DEFAULT_TIMEOUT_MS = "120000";
    BASH_MAX_TIMEOUT_MS = "600000";
    CLAUDE_DANGEROUSLY_DISABLE_SANDBOX = "true";
    CLAUDE_SKIP_PERMISSIONS = "true";
  };
}
