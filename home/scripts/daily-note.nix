# Same as /shell/daily-note.sh
{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/daily_note;

  daily-note = pkgs.writeShellScriptBin "daily-note" ''
    ${script}
  '';
in
{
  home.packages = [ daily-note ];
}
