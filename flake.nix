{
  description = ''
    not A very basic flake

    Forget everything you know about nix, this is just a framework to configure apps and dotfiles.
  '';

  inputs.dependencies.url = "path:./repository/flake-assembly/dependencies";

  outputs =
    { self, dependencies }:
    import ./repository/flake-assembly/outputs.nix (dependencies.inputs // { inherit self; });
}
