{
  description = "Public CI stand-in for the private Neovim input";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-26.05";
  inputs.home-manager.url = "github:nix-community/home-manager/release-26.05";

  outputs = _: {
    homeManagerModules.default =
      { lib, ... }:
      {
        options.neovimConfiguration = lib.mkOption {
          type = lib.types.attrsOf lib.types.str;
          default = { };
        };
      };
  };
}
