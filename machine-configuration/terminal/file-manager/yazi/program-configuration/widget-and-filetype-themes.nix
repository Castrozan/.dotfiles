{
  input = {
    border = {
      fg = "#89b4fa";
    };
    title = { };
    value = { };
    selected = {
      reversed = true;
    };
  };

  select = {
    border = {
      fg = "#89b4fa";
    };
    active = {
      fg = "#f5c2e7";
    };
    inactive = { };
  };

  tasks = {
    border = {
      fg = "#89b4fa";
    };
    title = { };
    hovered = {
      underline = true;
    };
  };

  which = {
    mask = {
      bg = "#313244";
    };
    cand = {
      fg = "#94e2d5";
    };
    rest = {
      fg = "#9399b2";
    };
    desc = {
      fg = "#f5c2e7";
    };
    separator = "  ";
    separator_style = {
      fg = "#585b70";
    };
  };

  help = {
    on = {
      fg = "#f5c2e7";
    };
    run = {
      fg = "#94e2d5";
    };
    desc = {
      fg = "#9399b2";
    };
    hovered = {
      bg = "#585b70";
      bold = true;
    };
    footer = {
      fg = "#45475a";
      bg = "#cdd6f4";
    };
  };

  filetype = {
    rules = [
      {
        mime = "image/*";
        fg = "#94e2d5";
      }
      {
        mime = "{audio,video}/*";
        fg = "#f9e2af";
      }
      {
        mime = "application/{,g}zip";
        fg = "#f5c2e7";
      }
      {
        mime = "application/x-{tar,bzip*,7z-compressed,xz,rar}";
        fg = "#f5c2e7";
      }
      {
        name = "*";
        fg = "#cdd6f4";
      }
      {
        name = "*/";
        fg = "#89b4fa";
      }
    ];
  };
}
