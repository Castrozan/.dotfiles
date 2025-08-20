{ latest, ... }:
{
  home.packages = [ latest.vial ];

  # xdg.desktopEntries.vial = {
  #   name = "Vial";
  #   genericName = "Keyboard Configurator";
  #   comment = "Configure your keyboard layouts and macros";
  #   exec = "${latest.vial}/bin/Vial";
  #   icon = "vial";
  #   terminal = false;
  #   type = "Application";
  #   categories = [ "Utility" ];
  # };
}
