{ pkgs }:
let
  inherit (pkgs) lib;

  marketplaceName = "dotfiles-mods";

  interactiveSessionModSources = {
    cache-tax = pkgs.fetchFromGitHub {
      owner = "Castrozan";
      repo = "cache-tax";
      rev = "5a567cf607237231da99850b50ea385791bb0e23";
      hash = "sha256-s/XZUfVfm7gzV+erl5FcU04o8aJC/AxSLuBc2lId2+A=";
    };
    crayon = pkgs.fetchFromGitHub {
      owner = "Castrozan";
      repo = "cc-crayon";
      rev = "a8ceb447b4a88fe0b55497f29856623479ba95fa";
      hash = "sha256-uG5Ar0onbU5cjVkNRcuTQjE8/b/g2B6TCztwyyuN3HI=";
    };
    image-view = pkgs.fetchFromGitHub {
      owner = "jarrodwatts";
      repo = "claude-image-view";
      rev = "370b8e7bc0708bebe9762e63534f7ca18bc3e802";
      hash = "sha256-cH2yGtD5k/zmOCE5WK8s9DoFicUnrCdzqfmp/GGoJW4=";
    };
    airquote = pkgs.fetchFromGitHub {
      owner = "Castrozan";
      repo = "airquote";
      rev = "7bb9679a8524a8c154b50afdab921c061df1f00b";
      hash = "sha256-/vHV1dLbT2GhfHGX6t4eIR/KakcnCEPXZpGQwno6aDA=";
    };
  };

  everySessionModSources = {
    compaction-brief = ./compaction-brief;
  };

  modSources = interactiveSessionModSources // everySessionModSources;

  pluginKeyOf = modName: "${modName}@${marketplaceName}";

  enabledPluginsFor =
    modSourcesByName:
    lib.mapAttrs' (modName: _: lib.nameValuePair (pluginKeyOf modName) true) modSourcesByName;

  marketplaceManifest = pkgs.writeText "marketplace.json" (
    builtins.toJSON {
      name = marketplaceName;
      owner.name = "Castrozan";
      plugins = lib.mapAttrsToList (modName: _: {
        name = modName;
        source = "./plugins/${modName}";
      }) modSources;
    }
  );
in
{
  marketplace = pkgs.runCommand "claude-${marketplaceName}-marketplace" { } ''
    mkdir -p "$out/.claude-plugin" "$out/plugins"
    cp ${marketplaceManifest} "$out/.claude-plugin/marketplace.json"
    ${lib.concatStrings (
      lib.mapAttrsToList (modName: modSource: ''
        cp -R ${modSource} "$out/plugins/${modName}"
      '') modSources
    )}
  '';

  pluginKeys = map pluginKeyOf (builtins.attrNames modSources);

  everySessionEnabledPlugins = enabledPluginsFor everySessionModSources;

  interactiveSessionEnabledPlugins = enabledPluginsFor interactiveSessionModSources;

  interactiveSessionPluginConfigs.${pluginKeyOf "airquote"}.options.dictionary =
    lib.concatStringsSep ", "
      [
        "Claude Code"
        "Codex"
        "OpenCode"
        "herdr"
        "clawde"
        "Nix"
        "nixpkgs"
        "NixOS"
        "nix-darwin"
        "home-manager"
        "agenix"
        "flake"
        "dotfiles"
        "worktree"
        "kira"
        "chise"
        "rin"
        "Betha"
        "Todoist"
        "Obsidian"
        "Quickshell"
        "Neovim"
        "LazyVim"
        "Cache Tax"
        "crayon"
        "Airquote"
      ];
}
