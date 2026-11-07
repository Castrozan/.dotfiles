{
  pkgs,
}:
let
  desktopComputerUse =
    pkgs.lib.head
      (import ../skills/workstation/desktop/install { inherit pkgs; }).packages;
in
pkgs.lib.optionalAttrs pkgs.stdenv.hostPlatform.isDarwin {
  desktop-computer-use = {
    type = "stdio";
    command = pkgs.lib.getExe desktopComputerUse;
  };
}
