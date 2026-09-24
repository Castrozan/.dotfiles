{
  config,
  pkgs,
  ...
}:
{
  assertions = [
    {
      assertion = config.hardware.nvidia.modesetting.enable;
      message = "NVIDIA modesetting is required — Wayland compositors (Hyprland, GNOME) cannot drive displays without kernel modesetting; without it you get a black screen or forced fallback to Xorg";
    }
    {
      assertion = config.hardware.nvidia.prime.sync.enable;
      message = "NVIDIA PRIME sync is required — the Dell G15 has an iGPU+dGPU topology where the display is wired through the AMD iGPU; sync mode routes all rendering through the dGPU to avoid tearing and microstutter";
    }
    {
      assertion = config.boot.kernelPackages.kernel.version == pkgs.linuxPackages_6_1.kernel.version;
      message = "LTS kernel 6.1.x is required — NVIDIA proprietary driver 550.x is only validated against 6.1 LTS; newer kernels cause module build failures or runtime crashes after suspend";
    }
  ];

  services.xserver.videoDrivers = [ "nvidia" ];

  boot.kernelPackages = pkgs.linuxPackages_6_1;

  hardware.nvidia = {
    # Pin to production 550.135 using mkDriver so it stays on that exact version.
    package = config.boot.kernelPackages.nvidiaPackages.mkDriver {
      version = "550.135";
      sha256_64bit = "sha256-ESBH9WRABWkOdiFBpVtCIZXKa5DvQCSke61MnoGHiKk=";
      sha256_aarch64 = "sha256-pum2JGz9KW/95QEI5M0Zv7bjiE0MDhQCvmqeQlMIJ/E=";
      openSha256 = "sha256-ulym4ke3Z8QofrqeVT8DSB6U8fM0fMq1DIfbB4ikn3s=";
      settingsSha256 = "sha256-4B61Q4CxDqz/BwmDx6EOtuXV/MNJbaZX+hj/Szo1z1Q=";
      persistencedSha256 = "sha256-fA3oaQflk7l4AupFeYazxl0gnm7qW82Ux4VKSJP6bGY=";
    };
    open = false;
    modesetting.enable = true;
    nvidiaSettings = true;

    powerManagement = {
      enable = false;
      finegrained = false;
    };

    prime = {
      sync.enable = true;
      offload.enable = false;
      amdgpuBusId = "PCI:4:0:0";
      nvidiaBusId = "PCI:1:0:0";
    };
  };

  boot.initrd.kernelModules = [
    "nvidia"
    "nvidia_modeset"
    "nvidia_uvm"
    "nvidia_drm"
  ];

  environment.systemPackages = with pkgs; [
    cudatoolkit
  ];

  environment.sessionVariables = {
    LIBVA_DRIVER_NAME = "nvidia";
    __GLX_VENDOR_LIBRARY_NAME = "nvidia";
    GBM_BACKEND = "nvidia-drm";
    NVD_BACKEND = "direct";
  };
}
