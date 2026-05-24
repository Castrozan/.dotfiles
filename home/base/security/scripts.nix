{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "agenix-edit" (builtins.readFile ./scripts/agenix-edit))
    (pkgs.writeShellScriptBin "agenix-edit-phone" (builtins.readFile ./scripts/agenix-edit-phone))
  ];
}
