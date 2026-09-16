{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "mouse-poll-rate" ''
      exec ${pkgs.python312}/bin/python3 ${./scripts}/mouse_poll_rate.py "$@"
    '')
  ];
}
