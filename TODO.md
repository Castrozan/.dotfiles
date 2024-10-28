
# TODO

- Ubuntu
  - [F] Convert all scripts to sh or make it POSIX compliant - Fuck POSIX let's do bash
  - [ ] Convert all scripts to bash
  - [ ] Remove auto import with files and use a single import with ". shell/src/file.sh"
  - [x] Fix install configs declaratively
    - Now the -d flag can be set to use de declarative install
  - [x] Add tmux tpm plugins
    - [ ] Remove tmp plugin folder on local ci
  - [ ] Add more lsp servers for nvim (lua, python, etc)
  - [ ] fix lazygit install. it is working but gives error on install
  - [ ] Configure nerd fonts for terminal
  - [ ] Remove all unnecessary output from scripts
  - [ ] Source the bashrc in the test ci
  - [ ] Run the install script with bash install.sh to make sure bash is the one to be changed
  - [ ] Migrate to zsh
  - [ ] Update README

- Nixos
  - [ ] Rewrite config to use home-manager by rayan's style
  - [ ] Zsh
  - [ ] Configure monitors with https://github.com/ryan4yin/nix-config/commit/ec485779ceb7afef5fbd12d3f80bbfe66e634f7f
