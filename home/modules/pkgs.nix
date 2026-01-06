{ pkgs, ... }:
{
  home.packages = with pkgs; [
    imv
    # pavucontrol # Removed: requires insecure qtwebengine-5.15.19 (Qt5 app)
    playerctl
    pulsemixer
    tree
  ];
}
