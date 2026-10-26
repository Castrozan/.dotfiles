{
  pkgs,
}:
let
  desktopComputerUse =
    pkgs.lib.head
      (import ../skills/workstation/desktop/install { inherit pkgs; }).packages;
in
{
  desktop-computer-use = {
    type = "stdio";
    command = pkgs.lib.getExe desktopComputerUse;
  };
}
