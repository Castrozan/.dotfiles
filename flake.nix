{
  description = ''
    not A very basic flake

    Forget everything you know about nix, this is just a framework to configure apps and dotfiles.
  '';

  # A flake takes four attributes: description, inputs, outputs and nixConfig

  # Inputs are the references used to build outputs, package sources, standalone packages...
  inputs.dependencies.url = "path:./repository/flake-assembly/dependencies";

  # Outputs are what the flake exposes, systems, modules, checks...
  outputs =
    { self, dependencies }:
    import ./repository/flake-assembly/outputs.nix (dependencies.inputs // { inherit self; });
}
