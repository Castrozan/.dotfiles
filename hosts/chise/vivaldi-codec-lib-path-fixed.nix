{ vivaldiPackages }:
vivaldiPackages.symlinkJoin {
  name = "vivaldi-codec-lib-path-fixed";
  paths = [ vivaldiPackages.vivaldi ];
  nativeBuildInputs = [ vivaldiPackages.makeWrapper ];
  postBuild = ''
    rm -f "$out/bin/vivaldi"
    makeWrapper "${vivaldiPackages.vivaldi}/bin/vivaldi" "$out/bin/vivaldi" \
      --prefix LD_LIBRARY_PATH : "${vivaldiPackages.vivaldi}/opt/vivaldi"
    for desktopFile in "$out"/share/applications/*.desktop; do
      realDesktopFile=$(readlink -f "$desktopFile")
      rm -f "$desktopFile"
      cp "$realDesktopFile" "$desktopFile"
      substituteInPlace "$desktopFile" \
        --replace-quiet "${vivaldiPackages.vivaldi}/bin/vivaldi" "$out/bin/vivaldi"
    done
  '';
}
