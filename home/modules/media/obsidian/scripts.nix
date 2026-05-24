{ pkgs, ... }:
let
  dailyNoteSource = pkgs.writeText "daily-note-source.py" (builtins.readFile ./scripts/daily_note.py);
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "daily-note" ''
      exec ${pkgs.python312}/bin/python3 ${dailyNoteSource} "$@"
    '')
    (pkgs.writeShellScriptBin "on" (builtins.readFile ./scripts/obsidian-quick-note))
  ];
}
