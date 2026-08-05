_:
let
  cursorIconPath = ./program-configuration/favicon.ico;
in
{
  xdg.desktopEntries.cursor = {
    name = "Cursor";
    exec = "cursor %F";
    icon = "${cursorIconPath}";
    type = "Application";
    categories = [
      "Development"
      "IDE"
    ];
    comment = "AI-first code editor";
  };
}
