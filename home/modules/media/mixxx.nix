{ pkgs, latest, ... }:
let
  musicLibraryPath = "$HOME/Music";

  ytmusicDownloadDependencies = [
    latest.yt-dlp
    pkgs.coreutils
  ];

  ytmusicDownload = pkgs.writeShellScriptBin "ytmusic-dl" ''
    set -euo pipefail
    export PATH="${pkgs.lib.makeBinPath ytmusicDownloadDependencies}:$PATH"

    MUSIC_DIR="${musicLibraryPath}"
    COOKIES_BROWSER="brave"

    usage() {
      echo "Usage: ytmusic-dl <command> [args]"
      echo ""
      echo "Commands:"
      echo "  search <query>       Search YouTube Music and download best match"
      echo "  playlist <url>       Download entire playlist to subfolder"
      echo "  url <url>            Download single track from URL"
      echo "  album <url>          Download album/playlist keeping folder structure"
      echo ""
      echo "Downloads go to: $MUSIC_DIR"
      echo "Uses cookies from $COOKIES_BROWSER for YouTube Music Premium quality"
      exit 1
    }

    [ $# -lt 1 ] && usage

    mkdir -p "$MUSIC_DIR"

    case "''${1}" in
      search)
        [ $# -lt 2 ] && { echo "Usage: ytmusic-dl search <query>" >&2; exit 1; }
        shift
        QUERY="$*"
        echo "Searching YouTube Music: $QUERY"
        yt-dlp \
          --cookies-from-browser "$COOKIES_BROWSER" \
          --extract-audio \
          --audio-format opus \
          --audio-quality 0 \
          --embed-thumbnail \
          --embed-metadata \
          --output "$MUSIC_DIR/%(title)s - %(artist)s.%(ext)s" \
          "ytsearch:$QUERY"
        echo "Done. Rescan library in Mixxx to see the new track."
        ;;

      playlist)
        [ $# -lt 2 ] && { echo "Usage: ytmusic-dl playlist <url>" >&2; exit 1; }
        PLAYLIST_URL="''${2}"
        echo "Downloading playlist: $PLAYLIST_URL"
        yt-dlp \
          --cookies-from-browser "$COOKIES_BROWSER" \
          --extract-audio \
          --audio-format opus \
          --audio-quality 0 \
          --embed-thumbnail \
          --embed-metadata \
          --output "$MUSIC_DIR/%(playlist_title)s/%(title)s - %(artist)s.%(ext)s" \
          --download-archive "$MUSIC_DIR/.ytmusic-archive.txt" \
          "$PLAYLIST_URL"
        echo "Done. Rescan library in Mixxx to see new tracks."
        ;;

      url)
        [ $# -lt 2 ] && { echo "Usage: ytmusic-dl url <url>" >&2; exit 1; }
        TRACK_URL="''${2}"
        echo "Downloading: $TRACK_URL"
        yt-dlp \
          --cookies-from-browser "$COOKIES_BROWSER" \
          --extract-audio \
          --audio-format opus \
          --audio-quality 0 \
          --embed-thumbnail \
          --embed-metadata \
          --output "$MUSIC_DIR/%(title)s - %(artist)s.%(ext)s" \
          "$TRACK_URL"
        echo "Done. Rescan library in Mixxx to see the new track."
        ;;

      album)
        [ $# -lt 2 ] && { echo "Usage: ytmusic-dl album <url>" >&2; exit 1; }
        ALBUM_URL="''${2}"
        echo "Downloading album: $ALBUM_URL"
        yt-dlp \
          --cookies-from-browser "$COOKIES_BROWSER" \
          --extract-audio \
          --audio-format opus \
          --audio-quality 0 \
          --embed-thumbnail \
          --embed-metadata \
          --output "$MUSIC_DIR/%(album)s/%(track_number)02d - %(title)s.%(ext)s" \
          --download-archive "$MUSIC_DIR/.ytmusic-archive.txt" \
          "$ALBUM_URL"
        echo "Done. Rescan library in Mixxx to see new tracks."
        ;;

      *)
        usage
        ;;
    esac
  '';
in
{
  home.packages = [
    pkgs.mixxx
    ytmusicDownload
  ];
}
