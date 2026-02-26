{ pkgs, ... }:
let
  intellijWithSplashDisabledAndWayland = pkgs.jetbrains.idea.overrideAttrs (previousAttrs: {
    postPatch = (previousAttrs.postPatch or "") + ''
      substituteInPlace bin/idea.sh \
        --replace-fail '-Dsplash=true' '-Dsplash=false'
    '';
    postInstall = (previousAttrs.postInstall or "") + ''
      rm "$out/bin/idea"
      ln -s "$out/idea/bin/idea.sh" "$out/bin/idea"
    '';
  });
in
{
  home.packages = [ intellijWithSplashDisabledAndWayland ];

  xdg.configFile."JetBrains/IntelliJIdea2025.2/idea64.vmoptions".text =
    "-Dawt.toolkit.name=WLToolkit\n";
}
