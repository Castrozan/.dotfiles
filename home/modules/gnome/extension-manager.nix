{ ... }:
{
  # Replicate the desktop entry to ~/.local/share/applications/
  # so GNOME can reliably find it
  xdg.desktopEntries."com.mattjakeman.ExtensionManager" = {
    name = "Extension Manager";
    genericName = "GNOME Shell Extensions Manager";
    exec = "extension-manager %U";
    icon = "com.mattjakeman.ExtensionManager";
    terminal = false;
    type = "Application";
    categories = [
      "GTK"
      "Utility"
    ];
    comment = "Manage GNOME Shell Extensions";
    startupNotify = true;
    mimeType = [ "x-scheme-handler/gnome-extensions" ];
  };
}
