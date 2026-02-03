{ pkgs, ... }:
{
  programs.lazygit = {
    enable = true;

    settings = {
      os = {
        shell = "${pkgs.fish}/bin/fish -i -c";
      };

      customCommands = [
        {
          key = "I";
          context = "global";
          description = "Quick-commit dotfiles + private-config submodule";
          command = ''dotfiles-quick-commit'';
          output = "popup";
        }
      ];
    };
  };
}
