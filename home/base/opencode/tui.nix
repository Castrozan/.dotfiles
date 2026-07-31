_:
let
  opencodeTuiSettings = {
    "$schema" = "https://opencode.ai/tui.json";
    theme = "kanagawa";
    mouse = true;
    diff_style = "auto";

    keybinds = {
      messages_undo = "ctrl+e,<leader>u";
    };

    attention = {
      enabled = true;
      notifications = true;
      sound = true;
      volume = 0.4;
    };

    prompt = {
      max_width = "auto";
    };
  };
in
{
  home.file.".config/opencode/tui.json".text = builtins.toJSON opencodeTuiSettings;
}
