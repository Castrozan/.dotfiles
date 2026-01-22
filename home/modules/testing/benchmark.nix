{ pkgs, ... }:
let
  benchmark-rebuild = pkgs.writeShellScriptBin "benchmark-rebuild" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.bc
        pkgs.gawk
        pkgs.util-linux
      ]
    }:$PATH"
    ${builtins.readFile ../../../bin/benchmark-rebuild}
  '';
  benchmark-shell = pkgs.writeShellScriptBin "benchmark-shell" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.bc
        pkgs.gawk
      ]
    }:$PATH"
    ${builtins.readFile ../../../bin/benchmark-shell}
  '';
in
{
  home.packages = [
    benchmark-rebuild
    benchmark-shell
  ];
}
