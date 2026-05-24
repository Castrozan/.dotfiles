{ pkgs, ... }:
let
  makeSummonBinary =
    binaryName: applicationName:
    pkgs.writeShellApplication {
      name = binaryName;
      runtimeInputs = [ pkgs.aerospace ];
      text = ''
        exec ${pkgs.bash}/bin/bash ${./summon-browser.sh} "${applicationName}"
      '';
    };
in
{
  home.packages = [
    (makeSummonBinary "summon-brave" "Brave Browser")
    (makeSummonBinary "summon-chrome" "Google Chrome")
  ];
}
