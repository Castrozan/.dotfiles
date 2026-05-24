{ pkgs, lib, ... }:
let
  vscodePinnedLinuxBuild = import ./vscode-pinned-linux-build.nix { inherit pkgs; };

  vscodePackageExposingChromeDevToolsProtocol =
    import ./vscode-package-exposing-chrome-devtools-protocol.nix
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
