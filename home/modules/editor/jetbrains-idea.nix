{ pkgs, ... }:
{
  home.packages = [ pkgs.jetbrains.idea ];

  xdg.configFile."JetBrains/IntelliJIdea2025.2/idea64.vmoptions".text = ''
    -Dawt.toolkit.name=WLToolkit
    -Dsplash=false
  '';

}
