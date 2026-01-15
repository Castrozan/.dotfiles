{ pkgs, lib, ... }:
let
  # Helper to create an Obsidian plugin package from GitHub release assets
  mkObsidianPlugin = { owner, repo, version, hash, hasStyles ? false }:
    pkgs.stdenv.mkDerivation {
      pname = "obsidian-plugin-${repo}";
      inherit version;

      src = pkgs.fetchzip {
        url = "https://github.com/${owner}/${repo}/releases/download/${version}/${repo}-${version}.zip";
        inherit hash;
        stripRoot = false;
      };

      installPhase = ''
        runHook preInstall
        mkdir -p $out
        cp main.js manifest.json $out/
        ${lib.optionalString hasStyles "cp -f styles.css $out/ 2>/dev/null || true"}
        runHook postInstall
      '';
    };

  # For plugins that don't have a zip, fetch individual files
  mkObsidianPluginFromFiles = { owner, repo, version, mainHash, manifestHash, stylesHash ? null }:
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

      stylesCss = if stylesHash != null then builtins.fetchurl {
        url = "https://github.com/${owner}/${repo}/releases/download/${version}/styles.css";
        sha256 = stylesHash;
      } else null;

      installPhase = ''
        runHook preInstall
        mkdir -p $out
        cp $mainJs $out/main.js
        cp $manifestJson $out/manifest.json
        ${lib.optionalString (stylesHash != null) "cp $stylesCss $out/styles.css"}
        runHook postInstall
      '';
    };

  # Plugin packages
  obsidian-read-it-later = mkObsidianPluginFromFiles {
    owner = "DominikPieper";
    repo = "obsidian-ReadItLater";
    version = "0.11.4";
    mainHash = "1fw2wwz6agll63s4j5kmb8qh82rk1m01hzvgx7qb3q8i6fdxzsar";
    manifestHash = "1j5gh3ndb69il4bf4khrsg96drhsaw3g7b62a887k1h6nhkar625";
  };

  obsidian-advanced-uri = mkObsidianPluginFromFiles {
    owner = "Vinzent03";
    repo = "obsidian-advanced-uri";
    version = "1.46.0";
    mainHash = "1b1p1h9h9kcy03myarwvznjsx8qpvfkrfzb5v4r5his2md182viq";
    manifestHash = "0flgg230q592al3z6kh3n8z2glh52a6q4wpar85l0aqnmcwi283c";
  };

  obsidian-vimrc-support = mkObsidianPluginFromFiles {
    owner = "esm7";
    repo = "obsidian-vimrc-support";
    version = "0.10.2";
    mainHash = "1qkc9rrh92hy5cbm0vqy4zbgccn53f1cll220mg51wpf35776qv8";
    manifestHash = "0mnh4yz53zx7lsyqpl4zjy3sb48l5mb83qw9jayqxf4iwd5mmpmj";
  };

  # Core plugins to enable (matching existing core-plugins.json)
  enabledCorePlugins = [
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
  ];
in
{
  programs.obsidian = {
    enable = true;
    package = null;  # Already installed via pkgs.nix

    vaults.vault = {
      target = "vault";

      settings = {
        appearance = {
          accentColor = "";
          textFontFamily = "FiraCode Nerd Font Mono";
          theme = "obsidian";
        };

        corePlugins = enabledCorePlugins;

        communityPlugins = [
          { pkg = obsidian-read-it-later; }
          { pkg = obsidian-advanced-uri; }
          { pkg = obsidian-vimrc-support; }
        ];

        hotkeys = {
          "file-explorer:reveal-active-file" = [
            { modifiers = [ "Mod" "Shift" ]; key = "E"; }
          ];
          "obsidian-read-it-later:save-clipboard-to-notice" = [
            { modifiers = [ "Mod" ]; key = "R"; }
          ];
        };
      };
    };
  };
}
