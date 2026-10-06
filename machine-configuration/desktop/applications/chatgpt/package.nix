{ pkgs, lib }:
let
  version = "26.928.21956";
  # Official Linux payload; no Debian maintainer scripts or security policy are installed.
  payload = pkgs.stdenvNoCC.mkDerivation {
    pname = "chatgpt-linux-payload";
    inherit version;
    src = pkgs.fetchurl {
      url = "https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt/chatgpt_${version}_amd64.deb";
      hash = "sha256-msjQcRtGATaNSd7dv1Co/lI1jLYbbZ96XBi0HtRQCtg=";
    };
    nativeBuildInputs = [
      pkgs.binutils
      pkgs.xz
    ];
    unpackPhase = ''
      ar p "$src" data.tar.xz | tar -xJf - ./usr
    '';
    dontConfigure = true;
    dontBuild = true;
    dontFixup = true;
    installPhase = ''
      mkdir -p "$out"
      cp -a usr/lib usr/share "$out/"
    '';
  };
in
# Keep the vendor binaries intact, with their normal Linux runtime and sandbox.
pkgs.buildFHSEnv {
  name = "chatgpt";
  inherit version;
  targetPkgs =
    p: with p; [
      alsa-lib
      at-spi2-core
      atk
      cairo
      cups
      curl
      dbus
      expat
      fontconfig
      freetype
      gdk-pixbuf
      git
      glib
      gtk3
      libGL
      libdrm
      libgbm
      libnotify
      libusb1
      libxkbcommon
      mesa
      nspr
      nss
      openssl
      pango
      stdenv.cc.cc
      systemd
      tpm2-tss
      vulkan-loader
      xdg-utils
      xorg.libX11
      xorg.libXcomposite
      xorg.libXdamage
      xorg.libXext
      xorg.libXfixes
      xorg.libXrandr
      xorg.libxcb
      xorg.libxshmfence
    ];
  runScript = "${payload}/lib/chatgpt/codex-launcher";
  extraInstallCommands = ''
    mkdir -p "$out/share/applications" "$out/share/pixmaps"
    cp ${payload}/share/applications/chatgpt.desktop "$out/share/applications/"
    cp ${payload}/share/pixmaps/chatgpt.png "$out/share/pixmaps/"
    substituteInPlace "$out/share/applications/chatgpt.desktop" \
      --replace-fail "Exec=chatgpt %U" "Exec=$out/bin/chatgpt %U"
  '';
  meta = {
    description = "Official ChatGPT desktop app for Linux";
    homepage = "https://learn.chatgpt.com/docs/linux/linux-app";
    license = lib.licenses.unfree;
    platforms = [ "x86_64-linux" ];
    mainProgram = "chatgpt";
  };
}
