_: {
  home.file = {
    # global rules for easy of management
    # Should change here and copy paste to cursor config manually
    ".dotfiles/home/modules/cursor/cursor-global-user-rules.md".source = ../../../agents/rules/evergreen-instructions.md;

    # local rules
    ".dotfiles/.cursor/evergreen-instructions.md".source = ../../../agents/rules/evergreen-instructions.md;
    ".dotfiles/.cursor/claude-code-agents.md".source = ../../../agents/rules/claude-code-agents.md;
  };
}
