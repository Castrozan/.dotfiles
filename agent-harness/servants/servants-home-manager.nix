{ pkgs, ... }:
let
  servantsDomain = ./.;
in
{
  # The Servant's name on the command line, for the surfaces that show a session
  # who it is. The Claude statusline is the caller today; it holds the session id
  # and nothing else, which is all the draw ever needed.
  home.packages = [
    (pkgs.writeShellScriptBin "servant-name" ''
      exec ${pkgs.python312}/bin/python3 ${servantsDomain}/servant_name.py "$@"
    '')
  ];
}
