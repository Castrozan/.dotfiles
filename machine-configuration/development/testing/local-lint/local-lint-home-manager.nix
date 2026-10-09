{ pkgs, ... }:
let
  tools = import ./local-lint-tools.nix { inherit pkgs; };
in
{
  home.packages = [
    tools.lint
    tools.coverage
  ];
}
