{ lib, ... }:
let
  karabinerMinimumVersionRequiredForSendUserCommand = "16.0.0";
in
{
  homebrew.casks = [ "karabiner-elements" ];

  system.activationScripts.postActivation.text = lib.mkAfter ''
    export REQUIRED_KARABINER_VERSION=${lib.escapeShellArg karabinerMinimumVersionRequiredForSendUserCommand}
    ${builtins.readFile ./check-karabiner-version.sh}
  '';
}
