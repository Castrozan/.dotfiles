{ pkgs }:
pkgs.openrgb.overrideAttrs (
  finalAttributes: _: {
    version = "1.1";

    src = pkgs.fetchFromCodeberg {
      owner = "OpenRGB";
      repo = "OpenRGB";
      tag = "release_${finalAttributes.version}";
      hash = "sha256-KPcud65Wx62JtIyqKI6P0TQLB2ohfM61WVgr2K47iZo=";
    };

    patches = [ ];

    postPatch = ''
      substituteInPlace \
        Controllers/FaustusController/RGBController_Faustus_Linux.cpp \
        Controllers/AsusTUFLaptopController/AsusTUFLaptopDetect_Linux.cpp \
        --replace-fail '/usr/bin/env chmod' '${pkgs.lib.getExe' pkgs.coreutils "chmod"}'
    '';
  }
)
