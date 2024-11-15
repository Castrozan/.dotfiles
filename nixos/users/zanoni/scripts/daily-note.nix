# Same as /shell/configs/daily-note.sh
{ pkgs, ... }:
let
  script = builtins.readFile ../../../../shell/configs/daily_note.sh;
in
let
  daily-note = pkgs.writeShellScriptBin "daily-note" ''
    ${script}
  '';
in
{
  environment.systemPackages = [ daily-note ];
}
