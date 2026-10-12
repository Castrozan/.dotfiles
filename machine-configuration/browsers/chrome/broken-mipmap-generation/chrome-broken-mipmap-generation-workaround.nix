{
  pkgs,
  chromePackage,
  hostname,
}:
let
  chromeWithoutBrokenMipmapGeneration = pkgs.symlinkJoin {
    name = "google-chrome-without-broken-mipmap-generation";
    paths = [ chromePackage ];
    nativeBuildInputs = [ pkgs.makeWrapper ];
    postBuild = ''
      rm "$out/bin/google-chrome-stable"
      makeWrapper "${chromePackage}/bin/google-chrome-stable" "$out/bin/google-chrome-stable" \
        --add-flags "--ozone-platform=wayland --disable-angle-features=recreate_mipmap_levels_before_generate"
    '';
  };

  chromeForMachine =
    if hostname == "chise" then chromeWithoutBrokenMipmapGeneration else chromePackage;
in
{
  inherit chromeForMachine;
}
