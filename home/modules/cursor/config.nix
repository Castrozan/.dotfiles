{ ... }:
{
  # global rules for easy of management
  # Should change here and copy paste to cursor config manually
  home.file.".dotfiles/home/modules/cursor/cursor-global-user-rules.md".source =
    ../../../agents/rules/user-rules.md;

  # local rules
  home.file.".dotfiles/.cursor/ai-interaction-guidelines.md".source =
    ../../../agents/rules/ai-interaction-guidelines.md;
  home.file.".dotfiles/.cursor/gnome-keybinding-debugging.md".source =
    ../../../agents/rules/gnome-keybinding-debugging.md;
  home.file.".dotfiles/.cursor/cursor-global-user-rules.md".source =
    ../../../agents/rules/user-rules.md;
}
