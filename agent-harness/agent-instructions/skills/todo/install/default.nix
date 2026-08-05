{ pkgs }:
let
  todoCliSource = ../scripts/todo_cli;

  todoCli = pkgs.writeShellScriptBin "todo" ''
    exec ${pkgs.python312}/bin/python ${todoCliSource}/todo.py "$@"
  '';
in
{
  packages = [ todoCli ];
}
