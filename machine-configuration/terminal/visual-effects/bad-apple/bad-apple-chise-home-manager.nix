{ pkgs, latest, ... }:
let
  videoUrls = [
    "https://www.youtube.com/watch?v=FtutLA63Cp8"
    "https://www.youtube.com/watch?v=CqaAs_3azSs"
    "https://www.youtube.com/watch?v=lX44CAz-JhU"
    "https://www.youtube.com/watch?v=djV11Xbc914"
    "https://www.youtube.com/watch?v=OBk3ynRbtsw"
    "https://www.youtube.com/watch?v=I03xFqbxUp8"
  ];

  deps = with pkgs; [
    latest.yt-dlp
    ffmpeg
    chafa
    coreutils
    gawk
  ];

  bad-apple-cmd = pkgs.writeShellScriptBin "bad-apple" ''
    export PATH="${pkgs.lib.makeBinPath deps}:$PATH"
    export BAD_APPLE_VIDEO_URLS=${pkgs.lib.escapeShellArg (pkgs.lib.concatStringsSep "\n" videoUrls)}
    ${builtins.readFile ./scripts/bad-apple}
  '';
in
{
  home.packages = [
    bad-apple-cmd
  ];
}
