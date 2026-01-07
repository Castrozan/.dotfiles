{ pkgs, ... }:
let
  # Custom GreatShot package - Rust-based screenshot tool for GNOME Wayland
  greatshot = pkgs.rustPlatform.buildRustPackage rec {
    pname = "greatshot";
    version = "0.1.0";

    src = pkgs.fetchFromGitHub {
      owner = "furqanalishah";
      repo = "greatshot";
      rev = "2f23a8d9cf780fe37d7b89f8cede7a520042b72f";
      sha256 = "sha256-5EwRVKMgGEqmz3mOq++RuJSHtHsXFg46obY45FnEeNs=";
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
      description = "Minimal, fast screenshot + annotation tool for Linux (GNOME Wayland)";
      homepage = "https://github.com/furqanalishah/greatshot";
      license = licenses.mit;
      maintainers = [ ];
      platforms = platforms.linux;
    };
  };
in
{
  home.packages = [ greatshot ];
}

