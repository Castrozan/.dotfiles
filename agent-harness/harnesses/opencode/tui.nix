_: {
  home.file.".config/opencode/cli.json".text = builtins.toJSON {
    "$schema" = "https://opencode.ai/v2/cli.json";
    theme.name = "kanagawa";
    plugins = [ "./herdr-session" ];
    mouse = true;
    diffs.view = "auto";
    session.sidebar = "hide";
    keybinds."session.undo" = "ctrl+e,<leader>u";
    attention = {
      notifications = true;
      sound = false;
      volume = 0.4;
    };
  };
}
