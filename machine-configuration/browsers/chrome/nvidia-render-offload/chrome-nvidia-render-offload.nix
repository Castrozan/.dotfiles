{
  pkgs,
  chromePackage,
  nvidiaRenderOffloadCommand,
}:
let
  chromeNvidiaRenderOffloadLauncher = pkgs.writeShellScript "chrome-nvidia-render-offload" ''
    export __EGL_VENDOR_LIBRARY_FILENAMES=/run/opengl-driver/share/glvnd/egl_vendor.d/10_nvidia.json
    exec ${pkgs.lib.escapeShellArg nvidiaRenderOffloadCommand} ${chromePackage}/bin/google-chrome-stable \
      --use-gl=angle --use-angle=gl-egl "$@"
  '';

  chromeWithNvidiaRenderOffload = pkgs.symlinkJoin {
    name = "google-chrome-with-nvidia-render-offload";
    paths = [ chromePackage ];
    postBuild = ''
      rm "$out/bin/google-chrome-stable"
      ln -s ${chromeNvidiaRenderOffloadLauncher} "$out/bin/google-chrome-stable"
    '';
  };
in
{
  inherit chromeWithNvidiaRenderOffload;
}
