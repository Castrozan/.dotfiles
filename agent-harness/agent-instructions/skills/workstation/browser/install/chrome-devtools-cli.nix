{
  pkgs,
  homeDir,
  nodejs,
  chromePackage,
}:
let
  upstream = import ./chrome-devtools-mcp-package.nix { inherit pkgs nodejs; };
  configuration = {
    upstreamExecutable = "${upstream}/bin/chrome-devtools";
    homeDirectory = homeDir;
    ffmpegExecutable = "${pkgs.ffmpeg}/bin/ffmpeg";
    chromeExecutable =
      if pkgs.stdenv.hostPlatform.isDarwin then
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
      else
        "${chromePackage}/bin/google-chrome-stable";
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
