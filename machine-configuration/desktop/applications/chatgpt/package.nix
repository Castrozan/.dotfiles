{ pkgs, lib }:
pkgs.stdenvNoCC.mkDerivation (finalAttributes: {
  pname = "chatgpt";
  version = "26.928.21956";
  # Official Linux payload; no Debian maintainer scripts or security policy are installed.
  src = pkgs.fetchurl {
    url = "https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt/chatgpt_${finalAttributes.version}_amd64.deb";
    hash = "sha256-msjQcRtGATaNSd7dv1Co/lI1jLYbbZ96XBi0HtRQCtg=";
  };
  nativeBuildInputs = with pkgs; [
    autoPatchelfHook
    binutils
    makeWrapper
    wrapGAppsHook3
    xz
  ];
  buildInputs = with pkgs; [
    alsa-lib
    at-spi2-core
    atk
    cairo
    cups
    dbus
    expat
    fontconfig
    freetype
    gdk-pixbuf
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
    xorg.libX11
    xorg.libXcomposite
    xorg.libXdamage
    xorg.libXext
    xorg.libXfixes
    xorg.libXrandr
    xorg.libxcb
    xorg.libxshmfence
  ];

  runtimeDependencies = map lib.getLib [
    pkgs.libGL
    pkgs.vulkan-loader
  ];

  unpackPhase = ''
    ar p "$src" data.tar.xz | tar -xJf - ./usr
  '';
  dontConfigure = true;
  dontBuild = true;
  dontStrip = true;
  installPhase = ''
    runHook preInstall
    mkdir -p "$out/bin"
    cp -a usr/lib usr/share "$out/"
    ln -s "$out/lib/chatgpt/codex-launcher" "$out/bin/chatgpt"
    substituteInPlace "$out/share/applications/chatgpt.desktop" \
      --replace-fail "Exec=chatgpt %U" "Exec=$out/bin/chatgpt %U"
    runHook postInstall
  '';
  preFixup = ''
    addAutoPatchelfSearchPath "${pkgs.qt5.qtbase}/lib" "${pkgs.qt6.qtbase}/lib"
    find "$out/lib/chatgpt/resources/app.asar.unpacked" -type d -name '*-musl' -prune -exec rm -r {} +
    find "$out/lib/chatgpt/resources/app.asar.unpacked" -type f -name '*.musl.node' -delete
  '';
  doInstallCheck = true;
  installCheckPhase = ''
    runHook preInstallCheck
    "$out/lib/chatgpt/resources/codex" --version
    "$out/lib/chatgpt/resources/cua_node/bin/node" --version
    "$out/lib/chatgpt/resources/rg" --version
    runHook postInstallCheck
  '';
  meta = {
    description = "Official ChatGPT desktop app for Linux";
    homepage = "https://learn.chatgpt.com/docs/linux/linux-app";
    license = lib.licenses.unfree;
    platforms = [ "x86_64-linux" ];
    mainProgram = "chatgpt";
  };
})
