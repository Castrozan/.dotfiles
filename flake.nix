{
  description = ''
    not A very basic flake

    Forget everything you know about nix, this is just a framework to configure apps and dotfiles.

    Inputs are declared in ./flake/inputs.nix, outputs in ./flake/outputs.nix.
  '';

  inputs = import ./flake/inputs.nix;

  outputs = inputs: import ./flake/outputs.nix inputs;
}
