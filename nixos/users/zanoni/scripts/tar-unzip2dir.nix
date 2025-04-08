{ pkgs, ... }:
let
  script = builtins.readFile ../../../../bin/tar-unzip2dir;
in
let
  tar-unzip2dir = pkgs.writeShellScriptBin "tar-unzip2dir" ''
    ${script}
  '';
in
{
  environment.systemPackages = [ tar-unzip2dir ];
}
