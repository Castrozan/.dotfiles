{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/benchmark-shell;
  benchmark-shell = pkgs.writeShellScriptBin "benchmark-shell" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.bc
        pkgs.gawk
      ]
    }:$PATH"
    ${script}
  '';
in
{
  home.packages = [ benchmark-shell ];
}
