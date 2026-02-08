_:
let
  opencodeRules = ''
    # OpenCode Project Context

    ${builtins.readFile ../../../agents/core.md}
  '';
in
{
  # Create AGENTS.md for dotfiles project
  home.file.".dotfiles/AGENTS.md".text = opencodeRules;
}
