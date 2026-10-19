{ pkgs }:
let
  inherit (pkgs) lib;

  marketplaceName = "dotfiles-mods";

  interactiveSessionModSources = {
    cache-tax = pkgs.applyPatches {
      name = "cache-tax-without-prompt-band";
      src = pkgs.fetchFromGitHub {
        owner = "karanb192";
        repo = "cache-tax";
        rev = "5cde9acc806728728cae70836db4f8f0655e0ff2";
        hash = "sha256-SD7NQmxGwnGYvJmXOfulVeGIPZXMGUT2UyRu3yNsa6s=";
      };
      patches = [ ./patches/hide-cache-tax-prompt-band.patch ];
    };
    crayon = pkgs.fetchFromGitHub {
      owner = "jonpojonpo";
      repo = "cc-crayon";
      rev = "f7c719eccd5d6eb48884e55b2e36b42e918109c5";
      hash = "sha256-AFOnQqrfmywcCBrdKqpUwJC8KSk9rT/Jm3dHxffhX0w=";
    };
    airquote = pkgs.fetchFromGitHub {
      owner = "karan-79";
      repo = "airquote";
      rev = "5e24a4a4047c3b8a02e05b01f403f5d02510cfe9";
      hash = "sha256-zJunklDAUnf/yvo/6xDYzFpfF5N/n85243FeKoGOH+o=";
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
