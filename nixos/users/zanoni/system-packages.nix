{ pkgs, inputs, ... }:
{
  # List of custom packages
  environment.systemPackages = [
    inputs.claude-desktop.packages.${pkgs.system}.claude-desktop-with-fhs
    inputs.codex-flake.packages.${pkgs.system}.default
    # Temporarily comment out whisper-input until we can configure it properly
    # inputs.whisper-input.defaultPackage.${pkgs.system}
  ];
}
