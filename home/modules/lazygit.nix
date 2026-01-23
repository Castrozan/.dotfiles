_: {
  programs.lazygit = {
    enable = true;

    # TODO: this is not working, so we're disabling it for now
    # The user config file /home/zanoni/.config/lazygit/config.yml must be migrated. Attempting to do this automatically.
    # The following changes were made:
    # - Moved git.paging object to git.pagers array
    # 2026/01/06 02:21:17 While attempting to write back migrated user config to /home/zanoni/.config/lazygit/config.yml, an error occurred: open /home/zanoni/.config/lazygit/config.yml: read-only file system
    # settings = {
    #   git = {
    #     paging = {
    #       colorArg = "always";
    #       pager = "delta --paging=never --detect-dark-light always";
    #     };
    #   };
    # };
  };
}
