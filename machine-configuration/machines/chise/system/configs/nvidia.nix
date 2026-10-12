{
  config,
  pkgs,
  ...
}:
{
  assertions = [
    {
      assertion = config.hardware.nvidia.modesetting.enable;
      message = "NVIDIA DRM modesetting is required for this host's Wayland sessions.";
    }
  ];

  services.xserver.videoDrivers = [ "nvidia" ];

  boot.kernelPackages = pkgs.linuxPackages_6_12;

  hardware.nvidia = {
    package = config.boot.kernelPackages.nvidiaPackages.mkDriver {
      version = "580.178.04";
      sha256_64bit = "sha256-WXWobuRb/8tib1GuM9EWmxCBhqLqR61lHnLxP6S21vk=";
      sha256_aarch64 = "sha256-71nsXSSFDhLW91UOwffPhNtTqEzpxj6zulXvXtDE8Ek=";
      openSha256 = "sha256-7eXEROG2rQK9+Ag26nG4jFPrnKeveVUQ0ugIAshJZPQ=";
      settingsSha256 = "sha256-KcrGHoR+ZMdsFyI4myU8/eVls2f8GkNSX/j2JnZndyM=";
      persistencedSha256 = "sha256-3Omj160wtWdKAZDzWt/m/cbUTQ9DMJ1rSxMrnIrKXiw=";
    };
    open = true;
    modesetting.enable = true;
    nvidiaSettings = true;

    powerManagement = {
      enable = false;
      finegrained = false;
    };

    prime = {
      sync.enable = false;
      offload = {
        enable = true;
        enableOffloadCmd = true;
      };
      amdgpuBusId = "PCI:5:0:0";
      nvidiaBusId = "PCI:1:0:0";
    };
  };

  boot.initrd.kernelModules = [
    "nvidia"
    "nvidia_modeset"
    "nvidia_uvm"
    "nvidia_drm"
  ];

  services.udev.extraRules = ''
    SUBSYSTEM=="drm", KERNEL=="card[0-9]*", SUBSYSTEMS=="pci", KERNELS=="0000:01:00.0", SYMLINK+="dri/nvidia-card"
    SUBSYSTEM=="drm", KERNEL=="card[0-9]*", SUBSYSTEMS=="pci", KERNELS=="0000:05:00.0", SYMLINK+="dri/amd-card"
  '';

  environment.systemPackages = with pkgs; [
    cudatoolkit
  ];

  environment.sessionVariables.AQ_DRM_DEVICES = "/dev/dri/amd-card:/dev/dri/nvidia-card";
}
