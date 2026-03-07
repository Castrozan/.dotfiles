{ username, pkgs, ... }:
{
  services.udev.extraRules = ''
    KERNEL=="hidraw*", ATTRS{idVendor}=="373b", ATTRS{idProduct}=="1040", MODE="0660", TAG+="uaccess"
  '';

  users.users.${username}.extraGroups = [ "input" ];

  environment.systemPackages = [ pkgs.evtest ];
}
