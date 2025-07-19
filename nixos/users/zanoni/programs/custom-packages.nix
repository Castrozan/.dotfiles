# Custom package configurations
{ pkgs, inputs, ... }:

{
  nixpkgs.overlays = [
    (final: prev: {
      whisper-input-cpu = inputs.whisper-input.defaultPackage.${pkgs.system}.overrideAttrs (oldAttrs: {
        # Configure whisper-input to use CPU instead of GPU
        configurePhase = ''
          export WHISPER_MODEL="small"
          # Force CPU usage instead of GPU
          export CUDA_VISIBLE_DEVICES=""
          # Use efficient CPU implementation (if supported)
          export OMP_NUM_THREADS=4
        '';
      });
    })
  ];

  environment.systemPackages = [
    pkgs.whisper-input-cpu
  ];
}
