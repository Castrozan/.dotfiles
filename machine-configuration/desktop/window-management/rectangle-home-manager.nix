{ config, ... }:
{
  home.activation.configureRectangleDefaults = config.lib.dag.entryAfter [ "writeBoundary" ] ''
    /usr/bin/defaults write com.knollsoft.Rectangle maximize -dict keyCode -int 3 modifierFlags -int 1048576
    /usr/bin/defaults write com.knollsoft.Rectangle leftHalf -dict keyCode -int 123 modifierFlags -int 1048576
    /usr/bin/defaults write com.knollsoft.Rectangle rightHalf -dict keyCode -int 124 modifierFlags -int 1048576
    /usr/bin/defaults write com.knollsoft.Rectangle topHalf -dict keyCode -int 126 modifierFlags -int 1048576
    /usr/bin/defaults write com.knollsoft.Rectangle bottomHalf -dict keyCode -int 125 modifierFlags -int 1048576
    /usr/bin/defaults write com.knollsoft.Rectangle restore -dict keyCode -int 3 modifierFlags -int 1572864
    /usr/bin/defaults write com.knollsoft.Rectangle launchOnLogin -bool true
    /usr/bin/defaults write com.knollsoft.Rectangle hideMenubarIcon -bool true
    /usr/bin/defaults write com.knollsoft.Rectangle SUEnableAutomaticChecks -bool false
    /usr/bin/defaults write com.knollsoft.Rectangle subsequentExecutionMode -int 1
  '';
}
