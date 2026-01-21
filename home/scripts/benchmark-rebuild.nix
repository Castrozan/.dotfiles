{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/benchmark-rebuild;
  benchmark-rebuild = pkgs.writeShellScriptBin "benchmark-rebuild" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.bc
        pkgs.gawk
        pkgs.util-linux
      ]
    }:$PATH"
    ${script}
  '';
in
{
  home.packages = [ benchmark-rebuild ];
}
