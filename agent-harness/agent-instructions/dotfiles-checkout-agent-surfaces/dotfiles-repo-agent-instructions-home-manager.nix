{ pkgs, ... }:
let
  projection = import ../instruction-projection.nix { inherit pkgs; };
  dotfilesRepoAgentInstructions = projection.instructionFile {
    name = "dotfiles-repository-agent-instructions.md";
    sources = [
      ../project-context/dotfiles-agent-instructions.md
      ../rebuild-guidance/rebuild-agent-instructions.md
    ];
    deployed = "/.dotfiles/AGENTS.md";
    destinations = { };
  };
in
{
  home.file.".dotfiles/AGENTS.md".source = dotfilesRepoAgentInstructions;
}
