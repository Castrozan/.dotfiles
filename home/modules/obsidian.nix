{ ... }:
{
  # Manage Obsidian configuration files declaratively
  # These files will be overwritten on each rebuild, ensuring consistency
  # Vault path is relative to home directory: ~/vault/.obsidian/
  home.file."vault/.obsidian/appearance.json" = {
    source = ./obsidian/config/appearance.json;
  };

  home.file."vault/.obsidian/hotkeys.json" = {
    source = ./obsidian/config/hotkeys.json;
  };

  home.file."vault/.obsidian/community-plugins.json" = {
    source = ./obsidian/config/community-plugins.json;
  };

  home.file."vault/.obsidian/core-plugins.json" = {
    source = ./obsidian/config/core-plugins.json;
  };
}

