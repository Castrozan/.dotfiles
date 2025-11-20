{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/tar-unzip2dir;
in
let
  tar-unzip2dir = pkgs.writeShellScriptBin "tar-unzip2dir" ''
    ${script}
  '';
in
{
  home.packages = [ tar-unzip2dir ];
}
