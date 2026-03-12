{ pkgs, config, ... }:
let
  spaceman = pkgs.stdenv.mkDerivation {
    pname = "spaceman";
    version = "1.0";

    src = pkgs.fetchurl {
      url = "https://github.com/Jaysce/Spaceman/releases/download/v1.0/Spaceman.1.0.dmg";
      sha256 = "1q2sk7jqshmkv5qbdnw8pscdkr3w69dhybna27d79hlzc02n12qd";
    };

    nativeBuildInputs = [ pkgs.undmg ];

    sourceRoot = "Spaceman.app";

    installPhase = ''
      mkdir -p $out/Applications/Spaceman.app
      cp -R . $out/Applications/Spaceman.app
    '';
  };
in
{
  home.packages = [ spaceman ];

  home.activation.configureSpacemanDefaults = config.lib.dag.entryAfter [ "writeBoundary" ] ''
    /usr/bin/defaults write com.jaysce.Spaceman SUEnableAutomaticChecks -bool false
  '';
}
