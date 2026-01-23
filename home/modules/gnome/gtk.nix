_:

{
  gtk = {
    enable = true;

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
