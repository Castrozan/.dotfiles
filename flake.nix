{
  description = ''
    not A very basic flake

    Forget everything you know about nix, this is just a framework to configure apps and dotfiles.

    Inputs live in the dependencies sub-flake taken as this flake's single input, and
    outputs in outputs.nix, to keep this file short. Nix refuses to force a thunk for
    `inputs`, so a sub-flake is the only indirection it accepts; importing the block
    from a plain .nix file fails.
  '';

  inputs.dependencies.url = "path:./repository/flake-assembly/dependencies";

  outputs =
    { self, dependencies }:
    import ./repository/flake-assembly/outputs.nix (dependencies.inputs // { inherit self; });
}
