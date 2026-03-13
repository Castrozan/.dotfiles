_:
let
  dotfilesAgentInstructions = ''
    # Dotfiles Agent Instructions

    ${builtins.readFile ../../../agents/core.md}
  '';
in
{
  home.file.".dotfiles/AGENTS.md".text = dotfilesAgentInstructions;
}
