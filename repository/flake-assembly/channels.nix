{ inputs, system }:
{
  pkgs = import inputs.nixpkgs {
    inherit system;
    config.allowUnfree = true;
  };

  unstable = import inputs.nixpkgs-unstable {
    inherit system;
    config.allowUnfree = true;
  };

  latest = import inputs.nixpkgs-latest {
    inherit system;
    config.allowUnfree = true;
  };
}
