{
  pkgs,
  homeDir,
  nodejs,
  chromePackage,
}:
let
  upstream = import ./chrome-devtools-mcp-package.nix { inherit pkgs nodejs; };
  nativeConfiguration = pkgs.writeText "chrome-consent-configuration.json" (
    builtins.toJSON {
      hyprctl = "${pkgs.hyprland}/bin/hyprctl";
      grim = "${pkgs.grim}/bin/grim";
      tesseract = "${pkgs.tesseract.override { enableLanguages = [ "eng" ]; }}/bin/tesseract";
      ydotool = "${pkgs.ydotool}/bin/ydotool";
      ydotoold = "${pkgs.ydotool}/bin/ydotoold";
      profileDirectory = "${homeDir}/.config/chrome-global";
      chromePackageDirectory = "${chromePackage}";
    }
  );
  nativePython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.pillow ]);
  configuration = {
    upstreamExecutable = "${upstream}/bin/chrome-devtools";
    homeDirectory = homeDir;
    ffmpegExecutable = "${pkgs.ffmpeg}/bin/ffmpeg";
    chromeExecutable =
      if pkgs.stdenv.hostPlatform.isDarwin then
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
      else
        "${chromePackage}/bin/google-chrome-stable";
    consentHelper = pkgs.lib.optionals pkgs.stdenv.hostPlatform.isLinux [
      "${nativePython}/bin/python3"
      "${./scripts/chrome-devtools}/chrome_consent_helper.py"
      "${nativeConfiguration}"
    ];
  };
  configurationFile = pkgs.writeText "chrome-devtools-cli-configuration.json" (
    builtins.toJSON configuration
  );
  command = pkgs.writeShellScriptBin "chrome-devtools" ''
    exec ${pkgs.python312}/bin/python3 ${./scripts/chrome-devtools}/chrome_devtools_command.py ${configurationFile} "$@"
  '';
in
command.overrideAttrs (previous: {
  passthru = (previous.passthru or { }) // {
    inherit configuration;
  };
})
