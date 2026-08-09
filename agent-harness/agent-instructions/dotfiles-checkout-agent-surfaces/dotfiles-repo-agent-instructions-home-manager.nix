_:
let
  dotfilesRepoAgentInstructions =
    builtins.readFile ../project-context/dotfiles-agent-instructions.md
    + "\n"
    + builtins.readFile ../rebuild-guidance/rebuild-agent-instructions.md;
in
{
  home.file = {
    ".dotfiles/AGENTS.md".text = dotfilesRepoAgentInstructions;
    ".dotfiles/CLAUDE.md".text = dotfilesRepoAgentInstructions;
  };
}
