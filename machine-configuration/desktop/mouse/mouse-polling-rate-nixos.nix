{ username, pkgs, ... }:
{
  services.udev.extraRules = ''
    KERNEL=="hidraw*", ATTRS{idVendor}=="373b", ATTRS{idProduct}=="103f", MODE="0660", GROUP="input"
    KERNEL=="hidraw*", ATTRS{idVendor}=="373b", ATTRS{idProduct}=="1040", MODE="0660", GROUP="input"
  '';

  users.users.${username}.extraGroups = [ "input" ];

  environment.systemPackages = [ pkgs.evtest ];
}
