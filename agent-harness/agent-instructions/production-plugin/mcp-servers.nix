{
  pkgs,
}:
let
  desktopComputerUse = import ../skills/workstation/desktop/install/computer-use-mcp-package.nix {
    inherit pkgs;
  };
in
pkgs.lib.optionalAttrs pkgs.stdenv.hostPlatform.isDarwin {
  desktop-computer-use = {
    type = "stdio";
    command = pkgs.lib.getExe desktopComputerUse;
  };
}
