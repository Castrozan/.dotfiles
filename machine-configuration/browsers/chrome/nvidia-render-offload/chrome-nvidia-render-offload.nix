{
  pkgs,
  chromePackage,
  nvidiaRenderOffloadCommand,
}:
let
  chromeWithNvidiaRenderOffload = pkgs.symlinkJoin {
    name = "google-chrome-with-nvidia-render-offload";
    paths = [ chromePackage ];
    nativeBuildInputs = [ pkgs.makeWrapper ];
    postBuild = ''
      rm "$out/bin/google-chrome-stable"
      makeWrapper ${pkgs.lib.escapeShellArg nvidiaRenderOffloadCommand} "$out/bin/google-chrome-stable" \
        --set __EGL_VENDOR_LIBRARY_FILENAMES /run/opengl-driver/share/glvnd/egl_vendor.d/10_nvidia.json \
        --add-flags "${chromePackage}/bin/google-chrome-stable --use-gl=angle --use-angle=gl-egl"
    '';
  };
in
{
  inherit chromeWithNvidiaRenderOffload;
}
