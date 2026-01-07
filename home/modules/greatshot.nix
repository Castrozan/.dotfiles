{ pkgs, ... }:
let
  # Custom GreatShot package - Rust-based screenshot tool for GNOME Wayland
  greatshot = pkgs.rustPlatform.buildRustPackage rec {
    pname = "greatshot";
    version = "0.1.0";

    src = pkgs.fetchFromGitHub {
      owner = "Castrozan";
      repo = "greatshot";
      rev = "c3905d77946a2bf9797472c7fb1a4bb28e2e34e8"; # Commit with capture mode and Ctrl+C support (to_unicode fix)
      sha256 = "sha256-MUihoQQWMIje+Ftw3yvourN6KWG2pAnS6s4REi7Wd1Q=";
    };

    cargoLock = {
      lockFile = "${src}/Cargo.lock";
    };

    nativeBuildInputs = with pkgs; [
      pkg-config
      gcc
      makeWrapper
    ];

    buildInputs = with pkgs; [
      gtk4
      libadwaita
      openssl
    ];

    meta = with pkgs.lib; {
      description = "Minimal, fast screenshot + annotation tool for GNOME Wayland";
      homepage = "https://github.com/Castrozan/greatshot";
      license = licenses.mit;
      maintainers = [ ];
      platforms = platforms.linux;
    };
  };
in
{
  home.packages = [ greatshot ];
}

