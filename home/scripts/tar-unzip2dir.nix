{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/tar-unzip2dir;

  tar-unzip2dir = pkgs.writeShellScriptBin "tar-unzip2dir" ''
    ${script}
  '';
in
{
  home.packages = [ tar-unzip2dir ];
}
