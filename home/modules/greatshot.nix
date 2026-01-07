{ pkgs, ... }:
let
  # Custom GreatShot package - Rust-based screenshot tool for GNOME Wayland
  # Using forked version with GREATSHOT_CAPTURE mode
  greatshot = pkgs.rustPlatform.buildRustPackage rec {
    pname = "greatshot";
    version = "0.1.0";

    src = pkgs.fetchFromGitHub {
      owner = "Castrozan";
      repo = "greatshot";
      rev = "ff7caa6a93c5956363cfc3cd1d9cfbd53b303080"; # Commit with capture mode support (env var)
      sha256 = "sha256-QA54Vs/wIZo4FoYwYCy21lZ133TFMlNL64V+6gZTNwE=";
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
      description = "Minimal, fast screenshot + annotation tool for GNOME Wayland (with --capture flag support)";
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

