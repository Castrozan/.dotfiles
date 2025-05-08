# Custom libinput quirks configuration for Dell G15 5515 touchpad
{ ... }:
{
  # Create local directory for libinput quirks
  environment.etc."libinput/local-overrides.quirks".text = ''
    [Dell G15 5515 Touchpad]
    MatchName=*Touchpad*
    MatchDMIModalias=dmi:*svnDell:pnG15*:pvrDellG155515*
    AttrPressureRange=4:25
    AttrPalmPressureThreshold=150
    AttrThumbPressureThreshold=200
  '';
}
