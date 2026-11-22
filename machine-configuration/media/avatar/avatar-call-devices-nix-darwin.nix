{ inputs, ... }:
{
  imports = [ inputs.avatar.darwinModules.default ];

  services.avatar.callDevices.enable = true;
}
