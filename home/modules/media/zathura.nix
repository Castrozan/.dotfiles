{
  pkgs,
  ...
}:
{
  programs.zathura = {
    enable = true;
    options = {
      statusbar-home-tilde = true;
      pages-per-row = 1;
      scroll-page-aware = true;
      scroll-step = 50;
      zoom-min = 10;
      zoom-max = 400;
      zoom-step = 10;
      default-bg = "#1e1e2e";
      default-fg = "#cdd6f4";
      statusbar-bg = "#313244";
      statusbar-fg = "#cdd6f4";
      inputbar-bg = "#313244";
      inputbar-fg = "#cdd6f4";
      notification-bg = "#313244";
      notification-fg = "#cdd6f4";
      notification-error-bg = "#a6e3a1";
      notification-error-fg = "#1e1e2e";
      notification-warning-bg = "#f9e2af";
      notification-warning-fg = "#1e1e2e";
      recolor = false;
      recolor-lightcolor = "#1e1e2e";
      recolor-darkcolor = "#cdd6f4";
      font = "monospace 12";
    };
    mappings = {
      q = "quit";
      "<C-d>" = "half-page-down";
      "<C-u>" = "half-page-up";
      D = "toggle_page_culling";
      i = "recolor";
      "<F5>" = "reload";
      "=" = "zoom in";
      "-" = "zoom out";
      "<C-a>" = "zoom fit-to-page";
    };
  };

  home.packages = [
    pkgs.zathura
  ];
}
