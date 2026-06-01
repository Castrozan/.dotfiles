{
  pkgs,
  inputs,
  ...
}:
let
  cmatrix-package = inputs.cmatrix.packages.${pkgs.stdenv.hostPlatform.system}.default;

  cmatrix-tmux-optimized = pkgs.writeShellScriptBin "cmatrix" ''
    asynchronous_scroll_when_multiplexed=()
    if [ -n "''${TMUX:-}" ]; then
      asynchronous_scroll_when_multiplexed+=(-a)
    fi
    exec ${cmatrix-package}/bin/cmatrix "''${asynchronous_scroll_when_multiplexed[@]}" "$@"
  '';
in
{
  home.packages = [
    cmatrix-tmux-optimized
  ];
}
