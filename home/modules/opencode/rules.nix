_:
let
  opencodeRules = ''
    # OpenCode Project Context

    ${builtins.readFile ../../../agents/rules/claude-code-agents.md}

    ${builtins.readFile ../../../agents/rules/evergreen-instructions.md}
  '';
in
{
  # Create AGENTS.md for dotfiles project
  home.file.".dotfiles/AGENTS.md".text = opencodeRules;
}
