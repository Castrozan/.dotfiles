{ pkgs, inputs, ... }:
{
  programs.lazygit = {
    enable = true;
    package = inputs.lazygit.packages.${pkgs.stdenv.hostPlatform.system}.default;

    settings = {
      os = {
        shell = "${pkgs.fish}/bin/fish -i -c";
      };

      customCommands = [
        {
          key = "I";
          context = "global";
          description = "Quick-commit dotfiles + private-config submodule";
          command = "dotfiles-quick-commit";
          output = "popup";
        }
      ];
    };
  };
}
