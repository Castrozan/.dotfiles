_:
let
  opencodeRules = ''
    # OpenCode Project Context

    ${builtins.readFile ../../../agents/rules/core.md}

    ${builtins.readFile ../../../agents/rules/gnome-keybinding-debugging.md}
  '';
in
{
  # Create AGENTS.md for dotfiles project
  home.file.".dotfiles/AGENTS.md".text = opencodeRules;
}
