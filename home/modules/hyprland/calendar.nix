# Calendar popup widget for waybar
# Self-contained GTK3 Python application with proper GObject introspection
{ pkgs, ... }:
let
  pythonEnv = pkgs.python3.withPackages (ps: [
    ps.pygobject3
    ps.pycairo
  ]);

  calendar-popup = pkgs.stdenv.mkDerivation {
    pname = "calendar-popup";
    version = "1.0.0";
    src = ../../../.config/waybar;

    nativeBuildInputs = with pkgs; [
      wrapGAppsHook3
      gobject-introspection
    ];

    buildInputs = with pkgs; [
      gtk3
      glib
      pythonEnv
    ];

    dontBuild = true;

    installPhase =
      let
        wrapper = pkgs.writeScript "calendar-popup-unwrapped" ''
          #!${pkgs.bash}/bin/bash
          export LOCALE_ARCHIVE="${pkgs.glibcLocales}/lib/locale/locale-archive"
          exec ${pythonEnv}/bin/python3 @out@/share/calendar-popup/calendar-popup.py "$@"
        '';
      in
      ''
        runHook preInstall
        mkdir -p $out/bin $out/share/calendar-popup
        cp calendar-popup.py $out/share/calendar-popup/
        substitute ${wrapper} $out/bin/calendar-popup --subst-var out
        chmod +x $out/bin/calendar-popup
        runHook postInstall
      '';
  };

  calendar-toggle = pkgs.writeShellScriptBin "calendar-toggle" ''
    if ${pkgs.procps}/bin/pkill -f "calendar-popup.py"; then
      exit 0
    else
      ${calendar-popup}/bin/calendar-popup &
    fi
  '';
in
{
  home.packages = [
    calendar-popup
    calendar-toggle
  ];
}
