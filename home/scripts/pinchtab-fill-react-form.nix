{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/pinchtab-fill-react-form;

  pinchtab-fill-react-form = pkgs.writeShellScriptBin "pinchtab-fill-react-form" ''
    ${script}
  '';
in
{
  home.packages = [ pinchtab-fill-react-form ];
}
