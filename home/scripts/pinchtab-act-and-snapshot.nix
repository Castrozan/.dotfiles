{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/pinchtab-act-and-snapshot;

  pinchtab-act-and-snapshot = pkgs.writeShellScriptBin "pinchtab-act-and-snapshot" ''
    ${script}
  '';
in
{
  home.packages = [ pinchtab-act-and-snapshot ];
}
