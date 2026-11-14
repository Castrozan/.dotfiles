{ pkgs }:
let
  inherit (pkgs) lib;

  interactiveSessionModSources = {
    cache-tax = pkgs.fetchFromGitHub {
      owner = "Castrozan";
      repo = "cache-tax";
      rev = "2e3796e2964f8d9c0afd647f767d46243d5a11c2";
      hash = "sha256-f713CgpvxI2SQLCRWt65q+e69dSCongxQJRSweAjTQ0=";
    };
    crayon = pkgs.fetchFromGitHub {
      owner = "Castrozan";
      repo = "cc-crayon";
      rev = "a8ceb447b4a88fe0b55497f29856623479ba95fa";
      hash = "sha256-uG5Ar0onbU5cjVkNRcuTQjE8/b/g2B6TCztwyyuN3HI=";
    };
    image-view = pkgs.fetchFromGitHub {
      owner = "jarrodwatts";
      repo = "claude-image-view";
      rev = "370b8e7bc0708bebe9762e63534f7ca18bc3e802";
      hash = "sha256-cH2yGtD5k/zmOCE5WK8s9DoFicUnrCdzqfmp/GGoJW4=";
    };
    airquote = pkgs.fetchFromGitHub {
      owner = "Castrozan";
      repo = "airquote";
      rev = "9d3a1cbf676707b110e8c5d638700c1fe627d6b1";
      hash = "sha256-j1xfp8n9WHEzghiTcRittVN+EWZY2BSsob4ncX033gY=";
    };
  };
in
{
  interactiveSessionModsDirectory = pkgs.linkFarm "claude-interactive-session-mods" interactiveSessionModSources;

  interactiveSessionPluginConfigs."airquote@inline".options.dictionary = lib.concatStringsSep ", " [
    "Claude Code"
    "Codex"
    "OpenCode"
    "herdr"
    "clawde"
    "Nix"
    "nixpkgs"
    "NixOS"
    "nix-darwin"
    "home-manager"
    "agenix"
    "flake"
    "dotfiles"
    "worktree"
    "kira"
    "chise"
    "rin"
    "Betha"
    "Todoist"
    "Obsidian"
    "Quickshell"
    "Neovim"
    "LazyVim"
    "Cache Tax"
    "crayon"
    "Airquote"
  ];
}
