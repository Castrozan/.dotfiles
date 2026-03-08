#!/usr/bin/env bats

setup_file() {
    REPO_DIR="$(cd "$BATS_TEST_DIRNAME" && git rev-parse --show-toplevel)"
    _evaluate_all_domain_modules
}

setup() {
    DOMAIN_CONFIG="$BATS_FILE_TMPDIR/domain-config.json"
}

_evaluate_all_domain_modules() {
    nix eval --expr '
      let
        dotfiles = builtins.getFlake (toString '"$REPO_DIR"');
        pkgs = import dotfiles.inputs.nixpkgs { system = "x86_64-linux"; config.allowUnfree = true; };
        unstable = import dotfiles.inputs.nixpkgs-unstable { system = "x86_64-linux"; config.allowUnfree = true; };
        latest = import dotfiles.inputs.nixpkgs-latest { system = "x86_64-linux"; config.allowUnfree = true; };
        hm = dotfiles.inputs.home-manager;

        cfg = (hm.lib.homeManagerConfiguration {
          inherit pkgs;
          extraSpecialArgs = {
            inherit unstable latest;
            inputs = dotfiles.inputs;
            isNixOS = false;
            username = "test";
            nixpkgs-version = "25.11";
            home-version = "25.11";
          };
          modules = [
            {
              home.username = "test";
              home.homeDirectory = "/home/test";
              home.stateVersion = "25.11";
            }
            '"$REPO_DIR"'/home/modules/terminal/fish.nix
            '"$REPO_DIR"'/home/modules/terminal/kitty.nix
            '"$REPO_DIR"'/home/modules/terminal/tmux.nix
            '"$REPO_DIR"'/home/modules/terminal/wezterm.nix
            '"$REPO_DIR"'/home/modules/terminal/atuin.nix
            '"$REPO_DIR"'/home/modules/terminal/yazi.nix
            '"$REPO_DIR"'/home/modules/editor/neovim.nix
            '"$REPO_DIR"'/home/modules/editor/zed-editor.nix
            '"$REPO_DIR"'/home/modules/browser/firefox.nix
            '"$REPO_DIR"'/home/modules/browser/chrome-global.nix
            '"$REPO_DIR"'/home/modules/desktop/fonts.nix
            '"$REPO_DIR"'/home/modules/desktop/fuzzel.nix
            '"$REPO_DIR"'/home/modules/desktop/clipse.nix
            '"$REPO_DIR"'/home/modules/dev/lazygit.nix
            '"$REPO_DIR"'/home/modules/dev/bruno.nix
            '"$REPO_DIR"'/home/modules/dev/devenv.nix
            '"$REPO_DIR"'/home/modules/dev/ccost.nix
            '"$REPO_DIR"'/home/modules/dev/mcporter.nix
            '"$REPO_DIR"'/home/modules/gaming/vesktop.nix
            '"$REPO_DIR"'/home/modules/gaming/cbonsai.nix
            '"$REPO_DIR"'/home/modules/gaming/cmatrix.nix
            '"$REPO_DIR"'/home/modules/gaming/install-nothing.nix
            '"$REPO_DIR"'/home/modules/gnome/dconf.nix
            '"$REPO_DIR"'/home/modules/gnome/gtk.nix
            '"$REPO_DIR"'/home/modules/media/ani-cli.nix
            '"$REPO_DIR"'/home/modules/media/bad-apple.nix
            '"$REPO_DIR"'/home/modules/media/youtube.nix
            '"$REPO_DIR"'/home/modules/media/suwayomi-server.nix
            '"$REPO_DIR"'/home/modules/voice/hey-bot.nix
            '"$REPO_DIR"'/home/modules/voice/voxtype.nix
            '"$REPO_DIR"'/home/modules/voice/whisp-away.nix
            '"$REPO_DIR"'/home/modules/voice/voice-pipeline.nix
            '"$REPO_DIR"'/home/modules/ollama
            '"$REPO_DIR"'/home/modules/network/network-optimization.nix
            '"$REPO_DIR"'/home/modules/network/tailscale-daemon.nix
            '"$REPO_DIR"'/home/modules/system/lid-switch-ignore.nix
            '"$REPO_DIR"'/home/modules/system/oom-protection.nix
            '"$REPO_DIR"'/home/modules/sourcebot
            '"$REPO_DIR"'/home/modules/opencode
            '"$REPO_DIR"'/home/modules/openclaw-mesh
            '"$REPO_DIR"'/home/modules/security
            '"$REPO_DIR"'/home/modules/testing
            '"$REPO_DIR"'/home/modules/audio
          ];
        }).config;

        fileNames = builtins.attrNames cfg.home.file;
        serviceNames = builtins.attrNames cfg.systemd.user.services;
        xdgConfigNames = builtins.attrNames cfg.xdg.configFile;
        packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;
        activationNames = builtins.attrNames cfg.home.activation;
        hasFile = name: builtins.hasAttr name cfg.home.file;
        hasService = name: builtins.hasAttr name cfg.systemd.user.services;
        hasXdgConfig = name: builtins.hasAttr name cfg.xdg.configFile;
        hasActivation = name: builtins.hasAttr name cfg.home.activation;
        hasFilePrefix = prefix: builtins.length (builtins.filter (n: builtins.substring 0 (builtins.stringLength prefix) n == prefix) fileNames) > 0;

      in {
        fishEnabled = cfg.programs.fish.enable;
        fishPluginCount = builtins.length cfg.programs.fish.plugins;
        carapaceEnabled = cfg.programs.carapace.enable;

        kittyEnabled = cfg.programs.kitty.enable;
        kittyTheme = cfg.programs.kitty.themeFile;

        tmuxEnabled = cfg.programs.tmux.enable;
        tmuxBaseIndex = cfg.programs.tmux.baseIndex;

        weztermEnabled = cfg.programs.wezterm.enable;

        atunEnabled = cfg.programs.atuin.enable;
        atunFishIntegration = cfg.programs.atuin.enableFishIntegration;

        yaziEnabled = cfg.programs.yazi.enable;

        neovimEnabled = cfg.programs.neovim.enable;
        hasNeovimConfig = hasFile ".config/nvim";

        firefoxEnabled = cfg.programs.firefox.enable;

        hasChromeDesktopEntry = builtins.hasAttr "chrome-global" cfg.xdg.desktopEntries;

        fontsEnabled = cfg.fonts.fontconfig.enable;

        fuzzelEnabled = cfg.programs.fuzzel.enable;

        hasClipseService = hasService "clipse";
        hasClipseConfig = hasXdgConfig "clipse/config.json";

        lazygitEnabled = cfg.programs.lazygit.enable;

        hasVesktopConfig = hasFile ".config/vesktop/settings/settings.json";

        gtkEnabled = cfg.gtk.enable;
        hasDconfSettings = builtins.hasAttr "org/gnome/desktop/interface" cfg.dconf.settings;

        gpgEnabled = cfg.programs.gpg.enable;
        gpgAgentEnabled = cfg.services.gpg-agent.enable;
        passwordStoreEnabled = cfg.programs.password-store.enable;
        hasPasswordStoreSyncService = hasService "password-store-git-sync";
        hasAgenixSecrets = builtins.length (builtins.attrNames cfg.age.secrets) > 0;
        hasSourceSecretsFile = hasFile ".secrets/source-secrets.sh";

        hasOllamaService = hasService "ollama";
        hasOllamaBin = hasFile ".local/bin/ollama";

        hasOpencodePackage = builtins.any (n: builtins.match ".*opencode.*" n != null) packageNames;

        hasOpenclavMeshConfig = hasXdgConfig "openclaw-mesh/config.json";
        hasOpenclavMeshOptions = builtins.hasAttr "mesh" cfg.openclaw;

        hasBluetoothAudioService = hasService "bluetooth-audio-autoswitch";

        hasNetworkOptimizationActivation = hasActivation "setupNetworkOptimization";
        hasOomProtectionActivation = hasActivation "setupOomProtection";
        hasLidSwitchActivation = hasActivation "setupLidSwitchIgnore";

        hasHeyBotOptions = builtins.hasAttr "hey-bot" cfg.services;

        hasSourcebotPackage = builtins.any (n: builtins.match ".*sourcebot.*" n != null) packageNames;

        hasBrunoConfig = hasXdgConfig "bruno/preferences.json";

        hasDevenvPackage = builtins.any (n: builtins.match ".*devenv.*" n != null) packageNames;
      }
    ' --impure --json 2>/dev/null > "$BATS_FILE_TMPDIR/domain-config.json"

    [ -s "$BATS_FILE_TMPDIR/domain-config.json" ] || {
        echo "Failed to evaluate domain modules" >&2
        cat "$BATS_FILE_TMPDIR/domain-config.json" 2>/dev/null
        return 1
    }
}

_check() {
    local key="$1"
    local expected="${2:-true}"
    [ "$(jq ".$key" "$DOMAIN_CONFIG")" = "$expected" ]
}

@test "terminal: fish shell enabled with plugins" {
    _check fishEnabled
    [ "$(jq '.fishPluginCount' "$DOMAIN_CONFIG")" -ge 3 ]
}

@test "terminal: carapace completion enabled" {
    _check carapaceEnabled
}

@test "terminal: kitty enabled with catppuccin theme" {
    _check kittyEnabled
    [ "$(jq -r '.kittyTheme' "$DOMAIN_CONFIG")" = "Catppuccin-Mocha" ]
}

@test "terminal: tmux enabled with base index 1" {
    _check tmuxEnabled
    _check tmuxBaseIndex 1
}

@test "terminal: wezterm enabled" {
    _check weztermEnabled
}

@test "terminal: atuin enabled with fish integration" {
    _check atunEnabled
    _check atunFishIntegration
}

@test "terminal: yazi file manager enabled" {
    _check yaziEnabled
}

@test "editor: neovim enabled with config directory" {
    _check neovimEnabled
    _check hasNeovimConfig
}

@test "browser: firefox enabled" {
    _check firefoxEnabled
}

@test "browser: chrome desktop entry registered" {
    _check hasChromeDesktopEntry
}

@test "desktop: fontconfig enabled" {
    _check fontsEnabled
}

@test "desktop: fuzzel launcher enabled" {
    _check fuzzelEnabled
}

@test "desktop: clipse clipboard service and config" {
    _check hasClipseService
    _check hasClipseConfig
}

@test "dev: lazygit enabled" {
    _check lazygitEnabled
}

@test "dev: bruno config deployed" {
    _check hasBrunoConfig
}

@test "dev: devenv package installed" {
    _check hasDevenvPackage
}

@test "gaming: vesktop config deployed" {
    _check hasVesktopConfig
}

@test "gnome: gtk theming enabled" {
    _check gtkEnabled
}

@test "gnome: dconf settings configured" {
    _check hasDconfSettings
}

@test "security: gpg and gpg-agent enabled" {
    _check gpgEnabled
    _check gpgAgentEnabled
}

@test "security: password-store enabled with sync service" {
    _check passwordStoreEnabled
    _check hasPasswordStoreSyncService
}

@test "security: agenix secrets configured" {
    _check hasAgenixSecrets
    _check hasSourceSecretsFile
}

@test "ollama: systemd service and binary" {
    _check hasOllamaService
    _check hasOllamaBin
}

@test "opencode: package installed" {
    _check hasOpencodePackage
}

@test "openclaw-mesh: config and options present" {
    _check hasOpenclavMeshConfig
    _check hasOpenclavMeshOptions
}

@test "audio: bluetooth autoswitch service" {
    _check hasBluetoothAudioService
}

@test "system: network optimization activation" {
    _check hasNetworkOptimizationActivation
}

@test "system: oom protection activation" {
    _check hasOomProtectionActivation
}

@test "system: lid switch ignore activation" {
    _check hasLidSwitchActivation
}

@test "voice: hey-bot options declared" {
    _check hasHeyBotOptions
}

@test "sourcebot: package installed" {
    _check hasSourcebotPackage
}
