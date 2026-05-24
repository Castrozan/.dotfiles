{ pkgs, ... }:
let
  wlrWhichKeyThemed = pkgs.writeShellScriptBin "wlr-which-key-themed" ''
    THEME_CONFIG="$HOME/.config/hypr-theme/current/theme/wlr-which-key.yaml"
    if [[ -f "$THEME_CONFIG" ]]; then
      exec ${pkgs.wlr-which-key}/bin/wlr-which-key "$THEME_CONFIG"
    else
      exec ${pkgs.wlr-which-key}/bin/wlr-which-key
    fi
  '';
in
{
  home.packages = [
    pkgs.wlr-which-key
    wlrWhichKeyThemed
  ];
}
