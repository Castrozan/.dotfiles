{ pkgs, ... }:

{
  # Enable graphics and CUDA support
  hardware.graphics = {
    enable = true;
    enable32Bit = true;
  };

  # Add minimal CUDA runtime package
  environment.systemPackages = with pkgs; [
    cudaPackages.cuda_cudart
  ];

  # Make sure the right GPU is used for CUDA apps without needing explicit offload
  environment.variables = {
    __NV_PRIME_RENDER_OFFLOAD = "1";
    __GLX_VENDOR_LIBRARY_NAME = "nvidia";
  };
}
