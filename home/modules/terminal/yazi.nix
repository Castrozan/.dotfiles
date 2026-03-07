_: {
  programs.yazi = {
    enable = true;

    # Shell integration (y wrapper that cds after exit)
    enableBashIntegration = true;
    enableFishIntegration = true;

    settings = {
      mgr = {
        show_hidden = true;
        ratio = [
          2
          4
          3
        ];
        show_symlink = true;
      };

      # Configure the which-key popup (shows key sequences)
      which = {
        sort_by = "key"; # Sort by key for easier scanning
        sort_sensitive = false;
        sort_reverse = false;
        sort_translit = false;
      };
    };

    # Keybindings with descriptive labels for the help menu
    keymap = {
      # Manager layer - main file navigation
      mgr.prepend_keymap = [
        # === HELP ===
        {
          on = "?";
          run = "help";
          desc = "Show keybindings help (filter by typing)";
        }
        {
          on = "<F1>";
          run = "help";
          desc = "Show keybindings help";
        }

        # === QUICK NAVIGATION ===
        {
          on = [
            "g"
            "h"
          ];
          run = "cd ~";
          desc = "Go to home directory";
        }
        {
          on = [
            "g"
            "c"
          ];
          run = "cd ~/.config";
          desc = "Go to ~/.config";
        }
        {
          on = [
            "g"
            "d"
          ];
          run = "cd ~/.dotfiles";
          desc = "Go to dotfiles";
        }
        {
          on = [
            "g"
            "D"
          ];
          run = "cd ~/Downloads";
          desc = "Go to Downloads";
        }
        {
          on = [
            "g"
            "p"
          ];
          run = "cd ~/projects";
          desc = "Go to projects";
        }
        {
          on = [
            "g"
            "t"
          ];
          run = "cd /tmp";
          desc = "Go to /tmp";
        }

        # === FILE OPERATIONS (with clear descriptions) ===
        {
          on = "y";
          run = "yank";
          desc = "Yank (copy) selected files";
        }
        {
          on = "x";
          run = "yank --cut";
          desc = "Cut selected files";
        }
        {
          on = "p";
          run = "paste";
          desc = "Paste yanked files";
        }
        {
          on = "P";
          run = "paste --force";
          desc = "Paste (overwrite existing)";
        }
        {
          on = "d";
          run = "remove";
          desc = "Move to trash";
        }
        {
          on = "D";
          run = "remove --permanently";
          desc = "Delete permanently (careful!)";
        }

        # === COPY PATH TO CLIPBOARD ===
        {
          on = [
            "c"
            "c"
          ];
          run = "copy path";
          desc = "Copy file path to clipboard";
        }
        {
          on = [
            "c"
            "d"
          ];
          run = "copy dirname";
          desc = "Copy directory path to clipboard";
        }
        {
          on = [
            "c"
            "f"
          ];
          run = "copy filename";
          desc = "Copy filename to clipboard";
        }
        {
          on = [
            "c"
            "n"
          ];
          run = "copy name_without_ext";
          desc = "Copy filename without extension";
        }

        # === SELECTION ===
        {
          on = "<Space>";
          run = [
            "select --state=none"
            "arrow 1"
          ];
          desc = "Toggle selection and move down";
        }
        {
          on = "v";
          run = "visual_mode";
          desc = "Enter visual selection mode";
        }
        {
          on = "V";
          run = "visual_mode --unset";
          desc = "Exit visual mode";
        }
        {
          on = "<C-a>";
          run = "select_all --state=true";
          desc = "Select all files";
        }
        {
          on = "<C-r>";
          run = "select_all --state=none";
          desc = "Invert selection";
        }

        # === VIEW/FILTER ===
        {
          on = ".";
          run = "hidden toggle";
          desc = "Toggle hidden files";
        }
        {
          on = "/";
          run = "find --smart";
          desc = "Find files (fuzzy)";
        }
        {
          on = "f";
          run = "filter --smart";
          desc = "Filter files (live)";
        }
        {
          on = "s";
          run = "search fd";
          desc = "Search with fd";
        }
        {
          on = "S";
          run = "search rg";
          desc = "Search file contents with ripgrep";
        }

        # === SORTING ===
        {
          on = [
            "o"
            "m"
          ];
          run = "sort modified --reverse";
          desc = "Sort by modified time (newest first)";
        }
        {
          on = [
            "o"
            "M"
          ];
          run = "sort modified";
          desc = "Sort by modified time (oldest first)";
        }
        {
          on = [
            "o"
            "n"
          ];
          run = "sort natural";
          desc = "Sort by name (natural)";
        }
        {
          on = [
            "o"
            "N"
          ];
          run = "sort natural --reverse";
          desc = "Sort by name (reverse)";
        }
        {
          on = [
            "o"
            "s"
          ];
          run = "sort size --reverse";
          desc = "Sort by size (largest first)";
        }
        {
          on = [
            "o"
            "e"
          ];
          run = "sort extension";
          desc = "Sort by extension";
        }

        # === TABS ===
        {
          on = "t";
          run = "tab_create --current";
          desc = "Create new tab in current dir";
        }
        {
          on = "T";
          run = "tab_create";
          desc = "Create new tab in home dir";
        }
        {
          on = "<C-c>";
          run = "tab_close";
          desc = "Close current tab";
        }
        {
          on = "[";
          run = "tab_switch -1 --relative";
          desc = "Switch to previous tab";
        }
        {
          on = "]";
          run = "tab_switch 1 --relative";
          desc = "Switch to next tab";
        }

        # === SHELL INTEGRATION ===
        {
          on = "!";
          run = "shell --interactive";
          desc = "Run shell command";
        }
        {
          on = "e";
          run = "shell --block --confirm '$EDITOR \"$@\"'";
          desc = "Edit in $EDITOR";
        }
        {
          on = "E";
          run = "shell --block --confirm 'code \"$@\"'";
          desc = "Open in VS Code";
        }
        {
          on = "<C-z>";
          run = "suspend";
          desc = "Suspend yazi (fg to resume)";
        }
      ];

      # Help layer - navigation within help menu
      help.prepend_keymap = [
        {
          on = "/";
          run = "filter";
          desc = "Filter keybindings";
        }
        {
          on = "<Esc>";
          run = "escape";
          desc = "Clear filter / close help";
        }
        {
          on = "q";
          run = "close";
          desc = "Close help";
        }
      ];
    };

    # Catppuccin Mocha theme
    theme = {
      mgr = {
        cwd = {
          fg = "#94e2d5";
        };
        hovered = {
          fg = "#1e1e2e";
          bg = "#89b4fa";
        };
        preview_hovered = {
          underline = true;
        };
        find_keyword = {
          fg = "#f9e2af";
          italic = true;
        };
        find_position = {
          fg = "#f5c2e7";
          bg = "reset";
          italic = true;
        };
        marker_copied = {
          fg = "#a6e3a1";
          bg = "#a6e3a1";
        };
        marker_cut = {
          fg = "#f38ba8";
          bg = "#f38ba8";
        };
        marker_selected = {
          fg = "#89b4fa";
          bg = "#89b4fa";
        };
        tab_active = {
          fg = "#1e1e2e";
          bg = "#cdd6f4";
        };
        tab_inactive = {
          fg = "#cdd6f4";
          bg = "#45475a";
        };
        tab_width = 1;
        count_copied = {
          fg = "#1e1e2e";
          bg = "#a6e3a1";
        };
        count_cut = {
          fg = "#1e1e2e";
          bg = "#f38ba8";
        };
        count_selected = {
          fg = "#1e1e2e";
          bg = "#89b4fa";
        };
        border_symbol = "│";
        border_style = {
          fg = "#7f849c";
        };
      };

      status = {
        separator_open = "";
        separator_close = "";
        separator_style = {
          fg = "#45475a";
          bg = "#45475a";
        };
        mode_normal = {
          fg = "#1e1e2e";
          bg = "#89b4fa";
          bold = true;
        };
        mode_select = {
          fg = "#1e1e2e";
          bg = "#a6e3a1";
          bold = true;
        };
        mode_unset = {
          fg = "#1e1e2e";
          bg = "#f2cdcd";
          bold = true;
        };
        progress_label = {
          fg = "#ffffff";
          bold = true;
        };
        progress_normal = {
          fg = "#89b4fa";
          bg = "#45475a";
        };
        progress_error = {
          fg = "#f38ba8";
          bg = "#45475a";
        };
        permissions_t = {
          fg = "#89b4fa";
        };
        permissions_r = {
          fg = "#f9e2af";
        };
        permissions_w = {
          fg = "#f38ba8";
        };
        permissions_x = {
          fg = "#a6e3a1";
        };
        permissions_s = {
          fg = "#7f849c";
        };
      };

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
    };
  };
}
