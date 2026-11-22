{ inputs, ... }:
{
  imports = [ inputs.avatar.nixosModules.default ];

  services.avatar.virtualCamera.enable = true;
}
