{ pkgs, ... }:
let
  hooksConfig = import ./hook-config.nix;
  pluginsConfig = import ./plugins.nix { inherit pkgs; };

  claudeKeybindings = {
    "$schema" = "https://www.schemastore.org/claude-code-keybindings.json";
    "$docs" = "https://code.claude.com/docs/en/keybindings";
    bindings = [
      {
        context = "Chat";
        bindings = {
          "ctrl+i" = "chat:undo";
        };
      }
    ];
  };

  claudeGlobalSettings = {
    installMethod = "native";
    model = "opus[1m]";
    effortLevel = "high";
    language = "english";
    spinnerTipsEnabled = false;
    dangerouslySkipPermissions = true;
    skipDangerousModePermissionPrompt = true;
    includeCoAuthoredBy = false;
    includeGitInstructions = false;
    showTurnDuration = false;
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
    hooks = hooksConfig;
  };

  claudeGlobalSettingsJson = builtins.toJSON claudeGlobalSettings;

  claudeDotfilesRules = ''
    # Claude Code Project Context

    ${builtins.readFile ../../../agents/core.md}
  '';

  claudeGlobalRules = ''
    ${builtins.readFile ../../../agents/core.md}
  '';
in
{
  home = {
    inherit (pluginsConfig) packages;
    file = {
      ".claude/.keep".text = "";
      ".claude/settings.json.nix-source".text = claudeGlobalSettingsJson;
      ".claude/keybindings.json".text = builtins.toJSON claudeKeybindings;
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
      BASH_ENV = "$HOME/.dotfiles/home/modules/terminal/shell/aliases.sh";
      CLAUDE_AUTOCOMPACT_PCT_OVERRIDE = "80";
      CLAUDE_CODE_DISABLE_TERMINAL_TITLE = "true";
    };

    activation.seedClaudeSettingsAsMutableFile = {
      after = [ "writeBoundary" ];
      before = [ ];
      data = ''
        CLAUDE_SETTINGS="$HOME/.claude/settings.json"
        NIX_SOURCE="$HOME/.claude/settings.json.nix-source"
        if [ -f "$NIX_SOURCE" ]; then
          if [ -f "$CLAUDE_SETTINGS" ]; then
            chmod 600 "$CLAUDE_SETTINGS" 2>/dev/null || true
            ${pkgs.jq}/bin/jq -s '.[0] * .[1]' "$CLAUDE_SETTINGS" "$NIX_SOURCE" > "$CLAUDE_SETTINGS.tmp" && mv "$CLAUDE_SETTINGS.tmp" "$CLAUDE_SETTINGS"
          else
            cp "$NIX_SOURCE" "$CLAUDE_SETTINGS"
          fi
          chmod 600 "$CLAUDE_SETTINGS"
        fi
      '';
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
