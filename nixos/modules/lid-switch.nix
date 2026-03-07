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
