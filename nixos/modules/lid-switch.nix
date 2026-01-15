# Module to disable lid switch actions (suspend/hibernate)
# Useful for laptops used as servers or with external monitors
{ config, lib, ... }:
let
  cfg = config.custom.lidSwitch;
in
{
  options.custom.lidSwitch = {
    disable = lib.mkEnableOption "disable lid switch suspend actions";
  };

  config = lib.mkIf cfg.disable {
    services.logind.settings.Login = {
      HandleLidSwitch = "ignore";
      HandleLidSwitchDocked = "ignore";
      HandleLidSwitchExternalPower = "ignore";
    };
  };
}
