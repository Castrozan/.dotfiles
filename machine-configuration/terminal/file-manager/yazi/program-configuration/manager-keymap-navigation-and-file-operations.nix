[
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
]
