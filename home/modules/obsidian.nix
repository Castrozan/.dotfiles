{ pkgs, ... }:
let
  # Fetch plugin files from GitHub releases
  mkPlugin =
    {
      owner,
      repo,
      version,
      mainHash,
      manifestHash,
      stylesHash ? null,
    }:
    pkgs.stdenv.mkDerivation {
      pname = "obsidian-plugin-${repo}";
      inherit version;
      dontUnpack = true;

      mainJs = builtins.fetchurl {
        url = "https://github.com/${owner}/${repo}/releases/download/${version}/main.js";
        sha256 = mainHash;
      };

      manifestJson = builtins.fetchurl {
        url = "https://github.com/${owner}/${repo}/releases/download/${version}/manifest.json";
        sha256 = manifestHash;
      };

      stylesCss =
        if stylesHash != null then
          builtins.fetchurl {
            url = "https://github.com/${owner}/${repo}/releases/download/${version}/styles.css";
            sha256 = stylesHash;
          }
        else
          null;

      installPhase = ''
        runHook preInstall
        mkdir -p $out
        cp $mainJs $out/main.js
        cp $manifestJson $out/manifest.json
        ${if stylesHash != null then "cp $stylesCss $out/styles.css" else ""}
        runHook postInstall
      '';
    };

  plugins = {
    obsidian-advanced-uri = mkPlugin {
      owner = "Vinzent03";
      repo = "obsidian-advanced-uri";
      version = "1.46.0";
      mainHash = "1b1p1h9h9kcy03myarwvznjsx8qpvfkrfzb5v4r5his2md182viq";
      manifestHash = "0flgg230q592al3z6kh3n8z2glh52a6q4wpar85l0aqnmcwi283c";
    };

    obsidian-excalidraw-plugin = mkPlugin {
      owner = "zsviczian";
      repo = "obsidian-excalidraw-plugin";
      version = "2.19.0";
      mainHash = "1jrx7fcpg3aczz3wigfkpcrzkf3ppy4izbgcxx998w0p2dnaqqm0";
      manifestHash = "0rvb2w0fhlqagx9jbxbxfv775nf4dhs1kkk22afccsbh1zcg0dmp";
      stylesHash = "1i74b4pk48ky6fjn8rdvn30h7avw987vdrz0xwhxw5z7k73ic1as";
    };

    obsidian-read-it-later = mkPlugin {
      owner = "DominikPieper";
      repo = "obsidian-ReadItLater";
      version = "0.11.4";
      mainHash = "1fw2wwz6agll63s4j5kmb8qh82rk1m01hzvgx7qb3q8i6fdxzsar";
      manifestHash = "1j5gh3ndb69il4bf4khrsg96drhsaw3g7b62a887k1h6nhkar625";
    };

    obsidian-vimrc-support = mkPlugin {
      owner = "esm7";
      repo = "obsidian-vimrc-support";
      version = "0.10.2";
      mainHash = "1qkc9rrh92hy5cbm0vqy4zbgccn53f1cll220mg51wpf35776qv8";
      manifestHash = "0mnh4yz53zx7lsyqpl4zjy3sb48l5mb83qw9jayqxf4iwd5mmpmj";
    };
  };

  pluginNames = builtins.attrNames plugins;
in
{
  # Install plugin directories to ~/vault/.obsidian/plugins/
  home.file =
    builtins.listToAttrs (
      map (name: {
        name = "vault/.obsidian/plugins/${name}";
        value = {
          source = plugins.${name};
          force = true;
        };
      }) pluginNames
    )
    // {
      # JSON configs - force = true ensures Obsidian overwrites are replaced on rebuild
      "vault/.obsidian/community-plugins.json" = {
        text = builtins.toJSON pluginNames;
        force = true;
      };

      "vault/.obsidian/core-plugins.json" = {
        text = builtins.toJSON [
          "file-explorer"
          "global-search"
          "switcher"
          "graph"
          "backlink"
          "canvas"
          "outgoing-link"
          "tag-pane"
          "page-preview"
          "daily-notes"
          "templates"
          "note-composer"
          "command-palette"
          "editor-status"
          "bookmarks"
          "outline"
          "word-count"
          "file-recovery"
          "sync"
        ];
        force = true;
      };

      "vault/.obsidian/appearance.json" = {
        text = builtins.toJSON {
          accentColor = "";
          textFontFamily = "FiraCode Nerd Font Mono";
          theme = "obsidian";
        };
        force = true;
      };

      "vault/.obsidian/hotkeys.json" = {
        text = builtins.toJSON {
          "file-explorer:reveal-active-file" = [
            {
              modifiers = [
                "Mod"
                "Shift"
              ];
              key = "E";
            }
          ];
          "obsidian-read-it-later:save-clipboard-to-notice" = [
            {
              modifiers = [ "Mod" ];
              key = "R";
            }
          ];
        };
        force = true;
      };
    };
}
