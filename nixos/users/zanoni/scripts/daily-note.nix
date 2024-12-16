# Same as /shell/configs/daily-note.sh
{pkgs, ...}: let
  script = builtins.readFile ../../../../bin/daily_note;
in let
  daily-note = pkgs.writeShellScriptBin "daily-note" ''
    ${script}
  '';
in {
  environment.systemPackages = [daily-note];
}
