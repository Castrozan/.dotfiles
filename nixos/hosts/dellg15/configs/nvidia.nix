{ config, pkgs, ... }:
{
  # Follow the instructions at https://nixos.wiki/wiki/Nvidia
  hardware.nvidia.modesetting.enable = true;
  hardware.nvidia.powerManagement.enable = true;
  hardware.nvidia.powerManagement.finegrained = false;
  hardware.nvidia.open = false;
  hardware.nvidia.nvidiaSettings = true;

  # TODO: fix, this seams to disable use of the dedicated GPU
  # Temporarily fixes the following.
  # Used to use this, but it's having the issue:
  # https://discourse.nixos.org/t/laptop-hangs-at-started-session-c1-of-user-gdm/26834
  # hardware.nvidia.package = config.boot.kernelPackages.nvidiaPackages.production;
  # Special config to load the latest (535 or 550) driver for the support of the 4070 SUPER
  hardware.nvidia.package =
    let
      rcu_patch = pkgs.fetchpatch {
        url = "https://github.com/gentoo/gentoo/raw/c64caf53/x11-drivers/nvidia-drivers/files/nvidia-drivers-470.223.02-gpl-pfn_valid.patch";
        hash = "sha256-eZiQQp2S/asE7MfGvfe6dA/kdCvek9SYa/FFGp24dVg=";
      };
    in
    config.boot.kernelPackages.nvidiaPackages.mkDriver {
      version = "535.154.05";
      sha256_64bit = "sha256-fpUGXKprgt6SYRDxSCemGXLrEsIA6GOinp+0eGbqqJg=";
      sha256_aarch64 = "sha256-G0/GiObf/BZMkzzET8HQjdIcvCSqB1uhsinro2HLK9k=";
      openSha256 = "sha256-wvRdHguGLxS0mR06P5Qi++pDJBCF8pJ8hr4T8O6TJIo=";
      settingsSha256 = "sha256-9wqoDEWY4I7weWW05F4igj1Gj9wjHsREFMztfEmqm10=";
      persistencedSha256 = "sha256-d0Q3Lk80JqkS1B54Mahu2yY/WocOqFFbZVBh+ToGhaE=";

      patches = [ rcu_patch ];
    };

  # Go back to offload mode but make it easier to use NVIDIA GPU
  hardware.nvidia.prime = {
    offload = {
      enable = true;
      enableOffloadCmd = true;
    };
    # Bus IDs from lspci
    amdgpuBusId = "PCI:4:0:0";
    nvidiaBusId = "PCI:1:0:0";
  };

  # Add nvidia-offload script
  environment.systemPackages = [
    (pkgs.writeShellScriptBin "nvidia-offload" ''
      export __NV_PRIME_RENDER_OFFLOAD=1
      export __NV_PRIME_RENDER_OFFLOAD_PROVIDER=NVIDIA-G0
      export __GLX_VENDOR_LIBRARY_NAME=nvidia
      export __VK_LAYER_NV_optimus=NVIDIA_only
      exec "$@"
    '')
  ];

  # Also make the NVIDIA GPU accessible for CUDA
  environment.variables = {
    CUDA_VISIBLE_DEVICES = "0";
    CUDA_PATH = "${pkgs.cudaPackages.cuda_cudart}";
  };
}
