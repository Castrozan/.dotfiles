{ config, pkgs, ... }:
{
  assertions = [
    {
      assertion = config.virtualisation.docker.enableOnBoot;
      message = "Docker must start on boot — containers created with --restart=always (Portainer, monitoring stacks) require the daemon running at boot to honor restart policies";
    }
    {
      assertion = config.virtualisation.libvirtd.enable;
      message = "libvirtd must be enabled — QEMU/KVM virtual machines require the libvirt daemon for lifecycle management, network bridging, and storage pool access";
    }
  ];

  virtualisation.docker = {
    enable = true;
    enableOnBoot = true;
  };
  users.extraGroups.docker.members = [ "zanoni" ];

  users.users.zanoni.extraGroups = [ "libvirtd" ];

  environment.systemPackages = with pkgs; [
    virt-manager
    virt-viewer
    spice
    spice-gtk
    spice-protocol
    virtio-win
    win-spice
    adwaita-icon-theme
    quickemu
  ];

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
