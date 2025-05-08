{
  config,
  lib,
  ...
}:
{
  # Enable graphics hardware
  hardware.graphics = {
    enable = true;
    enable32Bit = true; # Required for Steam and many games
  };

  # Enable NVIDIA driver
  services.xserver.videoDrivers = [ "nvidia" ];

  # NVIDIA settings
  hardware.nvidia = {
    # Enable modesetting
    modesetting.enable = true;

    # Enable power management (important for laptops)
    # Only enable basic power management in the default config
    # Fine-grained will be conditionally enabled in offload mode only
    powerManagement = {
      enable = true;
      finegrained = false; # Default is basic power management
    };

    # Use the open kernel module for better Wayland compatibility
    open = false; # RTX 3050 still works better with the proprietary driver

    # Enable settings utility
    nvidiaSettings = true;

    # Use the latest stable driver for RTX 3050 Mobile
    package = config.boot.kernelPackages.nvidiaPackages.stable;

    # PRIME configuration for hybrid graphics
    prime = {
      # Offload configuration (better battery life)
      offload = {
        enable = true;
        enableOffloadCmd = true; # Enables the nvidia-offload command
      };

      # Bus IDs for hybrid graphics (verified from lspci output)
      amdgpuBusId = "PCI:4:0:0"; # AMD Radeon Vega (integrated)
      nvidiaBusId = "PCI:1:0:0"; # NVIDIA RTX 3050 Mobile
    };
  };

  # Specialization for gaming mode with PRIME sync
  specialisation = {
    gaming-mode.configuration = {
      system.nixos.tags = [ "gaming-mode" ];
      hardware.nvidia = {
        # In gaming mode, disable power management completely
        # since the GPU will be always on
        powerManagement = {
          enable = lib.mkForce false;
          finegrained = lib.mkForce false;
        };

        prime = {
          # Disable offload and enable sync when in gaming mode
          # This provides better performance by using the NVIDIA GPU all the time
          offload.enable = lib.mkForce false;
          offload.enableOffloadCmd = lib.mkForce false;
          sync.enable = lib.mkForce true;
        };
      };
    };
  };

  # Runtime environment for better NVIDIA GPU support
  environment.sessionVariables = {
    # Improve PRIME render offload compatibility
    __GLX_VENDOR_LIBRARY_NAME = "nvidia";
    # Fix potential screen tearing
    __GL_SYNC_TO_VBLANK = "1";
    # Improve Vulkan performance on NVIDIA
    VK_ICD_FILENAMES = "/run/opengl-driver/share/vulkan/icd.d/nvidia_icd.x86_64.json";
  };

  # Add required kernel parameters for stable operation
  boot.kernelParams = [
    # Disable nouveau (open-source NVIDIA driver)
    "nvidia.NVreg_OpenRmEnableUnsupportedGpus=1"
    "nvidia-drm.modeset=1"
  ];

  # Blacklist nouveau
  boot.blacklistedKernelModules = [
    "nouveau"
    "nvidiafb"
  ];
}
