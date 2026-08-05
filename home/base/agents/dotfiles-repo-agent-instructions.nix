{ config, ... }:
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
    ".dotfiles/.githooks".source =
      config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/repository/git-hooks";
    ".dotfiles/.vscode".source =
      config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/repository/visual-studio-code-workspace";
  };
}
