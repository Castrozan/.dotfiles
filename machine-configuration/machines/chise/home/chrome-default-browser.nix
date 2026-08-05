{ lib, ... }:
{
  xdg.mimeApps = {
    enable = true;
    defaultApplications = {
      "text/html" = lib.mkForce "chrome-global.desktop";
      "text/xml" = lib.mkForce "chrome-global.desktop";
      "application/xhtml+xml" = lib.mkForce "chrome-global.desktop";
      "application/xml" = lib.mkForce "chrome-global.desktop";
      "x-scheme-handler/http" = lib.mkForce "chrome-global.desktop";
      "x-scheme-handler/https" = lib.mkForce "chrome-global.desktop";
    };
  };
}
