{
  lib,
  latest,
  isDarwin,
  ...
}:
let
  zathuraWithoutDisplayServerTests =
    (latest.zathuraPkgs.overrideScope (
      _final: previous: {
        zathura_core = previous.zathura_core.overrideAttrs (previousAttributes: {
          mesonFlags = previousAttributes.mesonFlags ++ [
            "-Dtests-x11=disabled"
            "-Dtests-wayland=disabled"
          ];
        });
      }
    )).zathuraWrapper;
in
{
  programs.zathura = {
    enable = true;
    package = lib.mkIf isDarwin zathuraWithoutDisplayServerTests;

    options = {
      statusbar-h-padding = 0;
      statusbar-v-padding = 0;
      page-padding = 1;
      selection-clipboard = "clipboard";
    };

    mappings = {
      u = "scroll half-up";
      d = "scroll half-down";
      D = "toggle_page_cache";
      r = "reload";
      R = "rotate";
      K = "zoom in";
      J = "zoom out";
      i = "recolor";
      p = "print";
    };
  };
}
