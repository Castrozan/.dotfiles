{ config, ... }:
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
    ".dotfiles/.githooks".source =
      config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/repository/git-hooks";
    ".dotfiles/.vscode".source =
      config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/repository/visual-studio-code-workspace";
  };
}
