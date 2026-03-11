{ pkgs, ... }:
{
  system.keyboard.enableKeyMapping = true;
  system.keyboard.userKeyMapping = [
    {
      HIDKeyboardModifierMappingSrc = 30064771296;
      HIDKeyboardModifierMappingDst = 30064771299;
    }
    {
      HIDKeyboardModifierMappingSrc = 30064771299;
      HIDKeyboardModifierMappingDst = 30064771296;
    }
    {
      HIDKeyboardModifierMappingSrc = 30064771300;
      HIDKeyboardModifierMappingDst = 30064771303;
    }
    {
      HIDKeyboardModifierMappingSrc = 30064771303;
      HIDKeyboardModifierMappingDst = 30064771300;
    }
  ];

  security.pam.services.sudo_local.touchIdAuth = true;

  system.stateVersion = 6;
  nixpkgs.hostPlatform = "aarch64-darwin";
}
