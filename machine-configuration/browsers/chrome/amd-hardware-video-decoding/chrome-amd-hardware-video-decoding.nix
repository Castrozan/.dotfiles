{
  pkgs,
  chromePackage,
  mesaPackage,
}:
pkgs.symlinkJoin {
  name = "google-chrome-with-amd-hardware-video-decoding";
  paths = [ chromePackage ];
  nativeBuildInputs = [ pkgs.makeWrapper ];
  postBuild = ''
    rm "$out/bin/google-chrome-stable"
    makeWrapper "${chromePackage}/bin/google-chrome-stable" "$out/bin/google-chrome-stable" \
      --set LIBVA_DRIVER_NAME radeonsi \
      --set LIBVA_DRIVERS_PATH "${mesaPackage}/lib/dri" \
      --set LIBGL_DRIVERS_PATH "${mesaPackage}/lib/dri" \
      --set GBM_BACKENDS_PATH "${mesaPackage}/lib/gbm" \
      --set __EGL_VENDOR_LIBRARY_FILENAMES "${mesaPackage}/share/glvnd/egl_vendor.d/50_mesa.json" \
      --add-flags "--use-gl=angle --use-angle=gl --render-node-override=/dev/dri/by-path/pci-0000:05:00.0-render"
  '';
}
