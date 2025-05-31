{ config, pkgs, ... }:
{
  # Follow the instructions at https://nixos.wiki/wiki/Nvidia
  hardware.nvidia.modesetting.enable = true;
  hardware.nvidia.powerManagement.enable = false;
  hardware.nvidia.powerManagement.finegrained = false;
  hardware.nvidia.open = false;
  hardware.nvidia.nvidiaSettings = true;
  hardware.nvidia.forceFullCompositionPipeline = true;

  # Load NVIDIA modules in initrd for proper initialization
  boot.initrd.kernelModules = [
    "nvidia"
    "nvidia_modeset"
    "nvidia_uvm"
    "nvidia_drm"
  ];
  boot.kernelParams = [
    "nvidia-drm.modeset=1"
    "nvidia.NVreg_UsePageAttributeTable=1"
  ];

  # Enable the production driver for best compatibility
  hardware.nvidia.package = config.boot.kernelPackages.nvidiaPackages.production;

  # PRIME configuration - sync mode makes NVIDIA the default GPU
  hardware.nvidia.prime = {
    # Using sync mode instead of offload for default NVIDIA rendering
    sync.enable = true;
    offload.enable = false;

    # Correct bus IDs based on lspci output
    amdgpuBusId = "PCI:4:0:0";
    nvidiaBusId = "PCI:1:0:0";
  };

  # Add CUDA toolkit and utilities
  environment.systemPackages = with pkgs; [
    # CUDA development tools
    cudatoolkit

    # Monitoring tools
    nvtopPackages.full
  ];

  # Environment variables for CUDA development and NVIDIA GPU use
  environment.variables = {
    CUDA_PATH = "${pkgs.cudatoolkit}";
    # Force OpenGL applications to use NVIDIA
    __GLX_VENDOR_LIBRARY_NAME = "nvidia";
    # GBM backend for Wayland
    GBM_BACKEND = "nvidia-drm";
    # For proper PRIME sync behavior
    __GL_SYNC_TO_VBLANK = "0";
  };
}
