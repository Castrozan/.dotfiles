{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/nix-gc;
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "nix-gc" script)
  ];
}
