{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "greatshot-capture" (builtins.readFile ./scripts/greatshot-capture))
    (pkgs.writeShellScriptBin "ksnip-annotate" (builtins.readFile ./scripts/ksnip-annotate))
  ];
}
