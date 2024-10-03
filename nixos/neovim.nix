{ pkgs, ... }:
{
  environment.variables.EDITOR = "nvim";

  # Global neovim configuration
  programs.neovim = {
    enable = true;
    viAlias = true;
    vimAlias = true;
    defaultEditor = true;
    configure = {
      customRC = ''
        set number
        set cc=80
        set list
        set listchars=tab:→\ ,space:·,nbsp:␣,trail:•,eol:¶,precedes:«,extends:»
        if &diff
          colorscheme blue
        endif
      '';
      packages.myVimPackage = with pkgs.vimPlugins; {
        start = [
          ctrlp
          nvim-treesitter.withAllGrammars
        ];
      };
    };
  };

}
