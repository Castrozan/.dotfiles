{
  config,
  pkgs,
  ...
}:
{
  services.xserver.videoDrivers = [ "nvidia" ];

  # Kernel version and NVIDIA-SMI version
  # uname -r
  # 6.1.141
  # nvidia-smi | head -n3
  # Sun Jun 29 23:05:49 2025
  # NVIDIA-SMI 550.135

  # Use the LTS kernel (6.1.x) that NVIDIA officially supports.
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

    # Optional power-mgmt flags (kept explicit but off)
    powerManagement = {
      enable = false;
      finegrained = false;
    };

    # PRIME block — keep only if you *really* have an iGPU+dGPU laptop
    prime = {
      sync.enable = true;
      offload.enable = false;
      amdgpuBusId = "PCI:4:0:0";
      nvidiaBusId = "PCI:1:0:0";
    };
  };

  # Load modules early
  boot.initrd.kernelModules = [
    "nvidia"
    "nvidia_modeset"
    "nvidia_uvm"
    "nvidia_drm"
  ];

  # CUDA & tooling
  environment.systemPackages = with pkgs; [
    cudatoolkit
    # nvtop-nvidia          # uncomment if you want GPU htop
  ];

  environment.sessionVariables = {
    LIBVA_DRIVER_NAME = "nvidia";
    __GLX_VENDOR_LIBRARY_NAME = "nvidia";
    GBM_BACKEND = "nvidia-drm";
    NVD_BACKEND = "direct";
  };
}
