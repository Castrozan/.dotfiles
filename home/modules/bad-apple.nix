{ pkgs, inputs, ... }:
let
  # Wrapper script to loop bad-apple-rs indefinitely
  bad-apple-loop = pkgs.writeShellScriptBin "bad-apple" ''
    while true; do
      ${inputs.bad-apple-rs.packages.${pkgs.stdenv.hostPlatform.system}.default}/bin/bad-apple-rs
      # Small delay between loops to prevent flickering
      sleep 0.5
    done
  '';
in
{
  home.packages = [
    inputs.bad-apple-rs.packages.${pkgs.stdenv.hostPlatform.system}.default
    bad-apple-loop
  ];
}
