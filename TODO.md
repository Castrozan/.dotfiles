
# TODO

- Config
  - [F] Convert all scripts to sh or make it POSIX compliant - Fuck POSIX let's do bash
  - [x] Convert all scripts to bash
  - [ ] Remove auto import with files and use a single import with ". shell/src/file.sh"
  - [x] Fix install configs declaratively
    - Now the -d flag can be set to use de declarative install
  - [x] Add tmux tpm plugins
    - [x] Remove tmp plugin folder on local ci
  - [ ] Add more lsp servers for nvim (lua, python, etc)
    - [ ] remove Mason
  - [ ] fix lazygit install. it is working but gives error on install
  - [ ] Configure nerd fonts for terminal
    - [ ] Jetbrains mono nerd fonts
  - [ ] Remove all unnecessary output from scripts
  - [ ] Source the bashrc in the test ci
  - [x] Run the install script with bash install.sh to make sure bash is the one to be changed
  - [ ] Migrate to zsh
  - [x] Update README
  - [x] clean kitty conf file
  - [ ] Fix fira-code font install
  - [ ] Fix nvm install
  - [ ] Fix obsidian install
  - [ ] fix fzf test
  - [x] Change color vars to begin with underline
  - [x] change bash location to #!/usr/bin/env bash
  - [ ] Make daily note to get undone todos from the day before to the current day
  - [x] fix bash_history

- Nixos
  - [ ] Rewrite config to use home-manager by rayan's style
  - [ ] Remove not used configs from rayan's config
  - [ ] Zsh
  - [ ] Configure monitors with https://github.com/ryan4yin/nix-config/commit/ec485779ceb7afef5fbd12d3f80bbfe66e634f7f

- Hyprland
  - [ ] Config bar
  - [ ] Config dmenu
  - [ ] Show workspaces on bar
  - [ ] Config audio selections