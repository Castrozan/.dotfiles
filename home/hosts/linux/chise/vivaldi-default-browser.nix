{ lib, ... }:
{
  xdg.mimeApps = {
    enable = true;
    defaultApplications = {
      "text/html" = lib.mkForce "vivaldi-stable.desktop";
      "text/xml" = lib.mkForce "vivaldi-stable.desktop";
      "application/xhtml+xml" = lib.mkForce "vivaldi-stable.desktop";
      "application/xml" = lib.mkForce "vivaldi-stable.desktop";
      "x-scheme-handler/http" = lib.mkForce "vivaldi-stable.desktop";
      "x-scheme-handler/https" = lib.mkForce "vivaldi-stable.desktop";
    };
  };
}
