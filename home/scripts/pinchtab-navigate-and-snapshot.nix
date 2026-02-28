{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/pinchtab-navigate-and-snapshot;

  pinchtab-navigate-and-snapshot = pkgs.writeShellScriptBin "pinchtab-navigate-and-snapshot" ''
    ${script}
  '';
in
{
  home.packages = [ pinchtab-navigate-and-snapshot ];
}
