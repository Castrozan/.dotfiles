{ pkgs, ... }:
let
  pythonSource = pkgs.writeText "git-toggle-user-source.py" (
    builtins.readFile ../../../home/modules/dev/scripts/git_toggle_user.py
  );
  git-toggle-user = pkgs.writeShellScriptBin "git-toggle-user" ''
    exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
  '';
in
{
  home.packages = [ git-toggle-user ];
}
