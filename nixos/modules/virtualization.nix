# TODO: review this
{ pkgs, ... }:
{
  # Docker configuration
  # TODO: check if this is breaking the system
  virtualisation.docker = {
    enable = true;

    # start dockerd on boot.
    # This is required for containers which are created with the `--restart=always` flag to work.
    enableOnBoot = true;
  };
  users.extraGroups.docker.members = [ "zanoni" ];

  # Virt-Manager
  # From https://github.com/TechsupportOnHold/Nixos-VM
  # Add user to libvirtd group
  users.users.zanoni.extraGroups = [ "libvirtd" ];

  # Install necessary packages
  environment.systemPackages = with pkgs; [
    virt-manager
    virt-viewer
    spice
    spice-gtk
    spice-protocol
    virtio-win
    win-spice
    adwaita-icon-theme
  ];

  # Manage the virtualisation services
  virtualisation = {
    libvirtd = {
      enable = true;
      qemu = {
        swtpm.enable = true;
      };
    };
    spiceUSBRedirection.enable = true;
  };
  services.spice-vdagentd.enable = true;
}
