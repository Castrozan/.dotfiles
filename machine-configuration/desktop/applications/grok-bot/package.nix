{ pkgs, lib }:
let
  pname = "grok-bot";
  version = "0.75.5";
  buildId = "e4789bbe423912faa668dc29e013436280428fe6";
  src = pkgs.fetchurl {
    url = "https://downloads.cursor.com/grokbot/stable/${buildId}/linux/x64/Grok_Bot_${version}.AppImage";
    hash = "sha256-XF72qTA2xn/ualMMSjIl0eCvoWmV2CmXHq8K/sUJaaA=";
  };
  extracted = pkgs.appimageTools.extract { inherit pname version src; };
in
pkgs.appimageTools.wrapType2 {
  inherit pname version src;
  extraInstallCommands = ''
    install -Dm444 ${extracted}/grok-bot.desktop "$out/share/applications/grok-bot.desktop"
    substituteInPlace "$out/share/applications/grok-bot.desktop" \
      --replace-fail "Exec=AppRun --no-sandbox %U" "Exec=$out/bin/grok-bot %U"
    cp -r ${extracted}/usr/share/icons "$out/share/"
  '';
  meta = {
    description = "Grok Bot desktop agent";
    homepage = "https://x.ai/bot";
    license = lib.licenses.unfree;
    platforms = [ "x86_64-linux" ];
    mainProgram = "grok-bot";
  };
}
