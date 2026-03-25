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
          "ctrl+e" = "chat:undo";
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
    showTurnDuration = true;
    teammateMode = "tmux";
    env = {
      CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS = "1";
      CLAUDE_ENABLE_STREAM_WATCHDOG = "1";
    };
    permissions = {
      defaultMode = "bypassPermissions";
      allow = [ "*" ];
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
  };

  claudeGlobalSettingsJson = builtins.toJSON claudeGlobalSettings;

  claudeDotfilesRules = ''
    @AGENTS.md

    ## Policies

    ### Compositor reload

    System rebuilds must never cause visual disruption to the running compositor. Configuration reloads that do not involve monitor hardware changes must not re-apply monitor rules, as mode negotiation causes DRM mode switches visible as screen blackouts. Compositor autoreload from config management symlink updates must be suppressed because the config directory symlink changes on every rebuild regardless of content. Only monitor hardware events — plug, unplug, manual toggle — justify full compositor reload with monitor re-application.
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
      ".claude/statusline-command.sh".source = ./scripts/statusline-command.sh;
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
