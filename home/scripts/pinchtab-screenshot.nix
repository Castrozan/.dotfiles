{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/pinchtab-screenshot;

  pinchtab-screenshot = pkgs.writeShellScriptBin "pinchtab-screenshot" ''
    ${script}
  '';
in
{
  home.packages = [ pinchtab-screenshot ];
}
