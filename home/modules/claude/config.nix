{ pkgs, ... }:
let
  hooksConfig = import ./hook-config.nix;
  pluginsConfig = import ./plugins.nix { inherit pkgs; };

  claudeGlobalSettings = {
    installMethod = "native";
    model = "opus";
    language = "english";
    spinnerTipsEnabled = false;
    dangerouslySkipPermissions = true;
    includeCoAuthoredBy = false;
    permissions = {
      defaultMode = "bypassPermissions";
      allow = [ "*" ];
      deny = [ ];
    };
    terminalShowHoverHint = false;
    composer = {
      shouldChimeAfterChatFinishes = true;
    };
    fileFiltering = {
      respectGitignore = true;
    };
    inherit (pluginsConfig) enabledPlugins;

    hooks = hooksConfig;
  };

  claudeDotfilesRules = ''
    # Claude Code Project Context

    ${builtins.readFile ../../../agents/rules/claude-code-agents.md}
  '';

  claudeGlobalRules = ''
    ${builtins.readFile ../../../agents/rules/evergreen-instructions.md}
  '';
in
{
  home = {
    inherit (pluginsConfig) packages;
    file = {
      ".claude/.keep".text = "";
      ".claude/settings.json".text = builtins.toJSON claudeGlobalSettings;
      ".dotfiles/CLAUDE.md".text = claudeDotfilesRules;
      ".claude/CLAUDE.md".text = claudeGlobalRules;
    };

    sessionVariables = {
      CLAUDE_CODE_SHELL = "${pkgs.bash}/bin/bash";
      CLAUDE_BASH_NO_LOGIN = "1";
      BASH_DEFAULT_TIMEOUT_MS = "120000";
      BASH_MAX_TIMEOUT_MS = "600000";
      CLAUDE_DANGEROUSLY_DISABLE_SANDBOX = "true";
      CLAUDE_SKIP_PERMISSIONS = "true";
      BASH_ENV = "$HOME/.dotfiles/shell/bash_aliases.sh";
    };

    activation.patchClaudeJsonInstallMethod = {
      after = [ "writeBoundary" ];
      before = [ ];
      data = ''
        CLAUDE_JSON="$HOME/.claude.json"
        if [ -f "$CLAUDE_JSON" ]; then
          ${pkgs.jq}/bin/jq '.installMethod = "native"' "$CLAUDE_JSON" > "$CLAUDE_JSON.tmp" && mv "$CLAUDE_JSON.tmp" "$CLAUDE_JSON"
        else
          echo '{"installMethod": "native"}' > "$CLAUDE_JSON"
        fi
      '';
    };
  };
}
