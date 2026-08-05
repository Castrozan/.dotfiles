{ pkgs, lib, ... }:
let
  vscodePinnedLinuxBuild = import ./visual-studio-code-pinned-linux-build.nix { inherit pkgs; };

  vscodePackageExposingChromeDevToolsProtocol =
    import ./visual-studio-code-package-exposing-chrome-devtools-protocol.nix
      {
        inherit pkgs lib;
        basePackage = vscodePinnedLinuxBuild;
        chromeDevToolsProtocolPort = "9333";
      };
in
{
  home.packages = [
    vscodePackageExposingChromeDevToolsProtocol
  ];
}
