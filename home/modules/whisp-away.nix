{ inputs, ... }:
{
  imports = [
    inputs.whisp-away.nixosModules.home-manager
  ];

  services.whisp-away = {
    enable = true;
    defaultModel = "base.en";
    defaultBackend = "whisper-cpp";
    accelerationType = "vulkan";
    useClipboard = false;
  };
}
