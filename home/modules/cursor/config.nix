_: {
  home.file = {
    # global rules for easy of management
    # Should change here and copy paste to cursor config manually
    ".dotfiles/home/modules/cursor/cursor-global-user-rules.md".source = ../../../agents/rules/core.md;

    # local rules
    ".dotfiles/.cursor/core.md".source = ../../../agents/rules/core.md;
    ".dotfiles/.cursor/gnome-keybinding-debugging.md".source =
      ../../../agents/rules/gnome-keybinding-debugging.md;
  };
}
