[
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
]
