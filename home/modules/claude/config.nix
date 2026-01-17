{ pkgs, ... }:
let
  # Hook scripts directory (relative to home)
  hooksPath = "~/.claude/hooks";

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
    enabledPlugins = {
      "claude-stt@jarrodwatts-claude-stt" = true;
      # LSP plugins
      "typescript-lsp@claude-plugins-official" = true;
      "jdtls-lsp@claude-plugins-official" = true;
      "nixd-lsp@custom-lsp" = true;
      "bash-lsp@custom-lsp" = true;
    };

    # Hooks configuration
    # hooks = {
    #   # PreToolUse hooks - run before tool execution
    #   PreToolUse = [
    #     {
    #       # Dangerous command blocker for Bash
    #       matcher = "Bash";
    #       hooks = [{
    #         type = "command";
    #         command = "python3 ${hooksPath}/dangerous-command-blocker.py";
    #         timeout = 5000;
    #       }];
    #     }
    #     {
    #       # Tmux reminder for long-running commands
    #       matcher = "Bash";
    #       hooks = [{
    #         type = "command";
    #         command = "python3 ${hooksPath}/tmux-reminder.py";
    #         timeout = 3000;
    #       }];
    #     }
    #     {
    #       # Git operation reminders
    #       matcher = "Bash";
    #       hooks = [{
    #         type = "command";
    #         command = "python3 ${hooksPath}/git-reminder.py";
    #         timeout = 5000;
    #       }];
    #     }
    #     {
    #       # Sensitive file guard for Edit/Write
    #       matcher = "Edit|Write";
    #       hooks = [{
    #         type = "command";
    #         command = "python3 ${hooksPath}/sensitive-file-guard.py";
    #         timeout = 3000;
    #       }];
    #     }
    #   ];

    #   # UserPromptSubmit hooks - run when user submits a prompt
    #   UserPromptSubmit = [
    #     {
    #       hooks = [{
    #         type = "command";
    #         command = "python3 ${hooksPath}/context-injector.py";
    #         timeout = 5000;
    #       }];
    #     }
    #   ];
    # };
  };

  claudeDotfilesRules = ''
    # Claude Code Project Context

    ${builtins.readFile ../../../agents/rules/core.md}

    ${builtins.readFile ../../../agents/rules/claude-code-agents.md}

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
    BASH_ENV = "$HOME/.dotfiles/shell/bash_aliases.sh";
  };

  # Patch ~/.claude.json to set installMethod (Claude Code reads from legacy file)
  home.activation.patchClaudeJson = {
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
}
