{ pkgs, ... }:

{
  gtk = {
    enable = true;

    theme = {
      name = "Adwaita-dark";
      package = pkgs.adwaita-icon-theme;
    };

    # Additional GTK3 configurations
    gtk3 = {
      extraConfig = {
        "gtk-application-prefer-dark-theme" = true;
      };
    };

    # Additional GTK4 configurations
    gtk4 = {
      extraConfig = {
        "gtk-application-prefer-dark-theme" = true;
      };
    };
  };
}
