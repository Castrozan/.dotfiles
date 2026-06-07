_:
let
  dotfilesRepoAgentInstructions =
    builtins.readFile ../../../agents/dotfiles.md
    + "\n"
    + builtins.readFile ../../../agents/snippets/rebuild.md;
in
{
  home.file = {
    ".dotfiles/AGENTS.md".text = dotfilesRepoAgentInstructions;
    ".dotfiles/CLAUDE.md".text = dotfilesRepoAgentInstructions;
  };
}
